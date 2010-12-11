#!/usr/bin/perl

BEGIN {
    unshift(@INC, "/home/carze/lib/perl/",
                  "home/carze/lib/perl/lib/perl5/site_perl/5.8.8/",
                  "/home/carze/lib/perl/lib64/perl5/site_perl/5.8.8/x86_64-linux-thread-multi",
                  "/home/carze/lib/perl/lib64/perl5/5.8.8/x86_64-linux-thread-multi/"
    );
}

use strict;
use warnings;
use FileHandle;
use File::Basename;
use File::Temp qw(tempdir);
use Pod::Usage;		
use Config::IniFiles;
use Archive::Tar;	
use DBI;
use DBD::mysql;
use CGI qw(:standard);
use Log::Log4perl qw(:easy);
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);

#-----------------------------------------
# GLOBALS/DEFAULTS
#-----------------------------------------
Log::Log4perl->easy_init( { level => "ALL", file => "/tmp/wwarn_calculations.log" } );
my $logger = get_logger();         
my $cfg;
my $markers_sample_size = {};
my $markers_genotyped = {};
my $haplotype_category = {'single' => 1, 'double' => 1, 'triple' => 1, 'quintuple' => 1};

tie %$cfg, 'Config::IniFiles', ( -file => '/export/projects/wwarn/conf/wwarn_calculations.ini' );

my $debug_lvl = $cfg->{'log'}->{'level'} ||= "DEBUG";
my $log_file = $cfg->{'log'}->{'file'} ||= "/tmp/wwarn_calculations.log";
Log::Log4perl->easy_init( { level => $debug_lvl, file => ">> $log_file" } );
$logger = get_logger();

my $db_server = $cfg->{'DB'}->{'server'};
my $db_name = $cfg->{'DB'}->{'name'};
my $db_user = $cfg->{'DB'}->{'username'};
my $db_pass = $cfg->{'DB'}->{'password'};

my $haplotype_tbl = $cfg->{'general'}->{'haplotype_table'};
my $out_dir = $cfg->{'general'}->{'output_dir'};

## Generate our temp directory that will house all our output files
my $tmp_dir = tempdir ( DIR => $out_dir );

## Initialize database connection
## Open a connection to our database
my $dbh = DBI->connect("DBI:mysql:database=$db_name;host=$db_server;mysql_multi_results=1", "$db_user", "$db_pass", 
   		                 { RaiseError => 1, PrintError => 1 }) || $logger->logdie("Could not connect to database $DBI::errstr");

## Start out by parsing our haplotype table which will be required 
## to generate the sample sizes and prevelances for our haplotypes.
my $haplotypes = _parse_haplotype_table($haplotype_tbl);

## We need to first parse through our data and tabulate the sample size data
($markers_sample_size, $markers_genotyped) = get_sample_size_data($haplotypes);

## With sample size data and genotyped data in hand we can go ahead and calculate the prevalance by
## both STUDY + SITE and STUDY + SITE + AGE GROUP
my $prevalence_data = calculate_prevalence_data($markers_sample_size, $markers_genotyped);

## Once all data is present we can write it all out to a tarball file with four text files containing 
## calculations
##
##      1.) Sample size by STUDY + SITE
##      2.) Sample size by STUDY + SITE + AGE GROUP
##      3.) Prevalence by STUDY + SITE
##      4.) Prevalence by STUDY + SITE + AGE GROUP
my $tar_outfile = write_output_tarball($markers_sample_size, $prevalence_data, $tmp_dir);

## Return file to requestee
open (DLFILE, "< $tar_outfile") or $logger->logdie("Could not open tarball $tar_outfile: $!");
my @fileholder = <DLFILE>;
close (DLFILE);

print header( 
            -type => 'application/x-download',
            -content_encoding => "tar",
            -attachment => "wwarn_calculations.tar" );
print @fileholder;

###############################################################################
#####                          SUBROUTINES                                #####
###############################################################################

sub get_sample_size_data {
	my $haplotypes = shift;
	my $sample_size_data = {};
	my $genotyped = {};
	
    foreach my $category (keys %$haplotype_category) {
        my $procedure_call;
        my $sth;
        my $db_results;

        ## Our haplotype data can be classified into several categories:
        ##
        ## 1.) Single markers - These are single markers (i.e. pfcrt 76 T)
        ## 2.) Combination markers - These are a mixture of markers e.g.
        ##          pfcrt76T + pfcrt76K/T = Double mixed
        ##
        ## These must each be tabulated utilizing a similar but slightly 
        ## different procedure
        if ($category eq "single") {
            $procedure_call = "call total_genotyped()";
            $sth = $dbh->prepare($procedure_call);
            $sth->execute();
            $db_results = $sth->fetchall_arrayref();
            
            calculate_single_sample_size_data($db_results, $sample_size_data, $genotyped);
        } else {
            ## When we are working with double, triple, or quintuple haplotypes we need
            ## to parse through our haplotype table.
            foreach my $haplotype_name (keys %{ $haplotypes->{$category} }) {
                my @query_parameters = @{ $haplotypes->{$category}->{$haplotype_name} };
                my $query_param_size = $#query_parameters + 1;
                
                ## Execute two SQL calls, one for grouping by study and the other by age
                foreach my $group_category ("study", "age") {
	                $procedure_call = "call " . $category . "_haplotype_sample_size(" . 
	                                    ("?, "x $query_param_size) . "?)";
	                $sth = $dbh->prepare($procedure_call);
	                $sth->execute(@query_parameters, $group_category);        
	                $db_results = $sth->fetchall_arrayref();
	                     
	                calculate_combination_sample_size_data($db_results, $genotyped, $group_category, $haplotype_name);                                                 
                }
            }
        }        
    }
    
    return ($sample_size_data, $genotyped);
}

#-----------------------------------------
# parse single marker data from the WWARN
# database and tabulate sample size +
# genotyped information
#-----------------------------------------
sub calculate_single_sample_size_data {
	my ($results, $sample_size, $geno_count) = @_;
	
	## For single marker sample size we must tabulate two
	## statistics:
	##
	## 1.) How many markers were seen as a specific locus name + 
	##     locus position combination (i.e. count how many pfcrt76 genotypes)
	## 2.) The specific genotype count of locus name + locus position + SNP
	##     i.e. count of pfcrt76T genotypes (we only want mutant + mixed types counted here)
	##
	## These must all be grouped by STUDY and SITE as well as STUDY and SITE and
	## binned by the following age groups:
	##
	##     a.) < 1 year
	##     b.) < 5 years
	##     c.) < 10 years
	##     d.) >= 10 years
	foreach my $row (@$results) {
		my $study_id = $row->[0];
		my $country = $row->[1];
		my $site = $row->[2];
		my $age = $row->[3];
		my $investigator = $row->[4];
		my $locus_name = $row->[5];
		my $locus_pos = $row->[6];
		my $genotype_value = $row->[7];
		my $mutant_status = $row->[8];
		
        ## Need to mesh together a marker that will be used as a key in our
        ## genotyped count hash
		my $marker = $locus_name . "_" . $locus_pos . "_"  .$genotype_value;
		$sample_size->{$study_id}->{'investigator'} = $investigator;
		$sample_size->{$study_id}->{$site}->{'country'} = $country;
				
        ## STUDY + SITE sample size and genotyped
        $sample_size->{$study_id}->{$site}->{$locus_name}->{$locus_pos}->{'sample_size'}++;
        $geno_count->{$study_id}->{$site}->{$marker}->{'genotyped'}++ if ($mutant_status ne "Wild");
        
        ## STUDY + SITE + age group sample size and genotyped (only do this if age is not NULL)
        next unless ( defined($age) );
        if ($age < 1) {
            $sample_size->{$study_id}->{$site}->{$locus_name}->{$locus_pos}->{'< 1 year'}++;
            $geno_count->{$study_id}->{$site}->{$marker}->{'< 1 year'}++ if ($mutant_status ne "Wild");	
        } 
        if ($age < 5) {
            $sample_size->{$study_id}->{$site}->{$locus_name}->{$locus_pos}->{'< 5 years'}++;
            $geno_count->{$study_id}->{$site}->{$marker}->{'< 5 years'}++ if ($mutant_status ne "Wild");          	
        }
        if ($age < 10) {
            $sample_size->{$study_id}->{$site}->{$locus_name}->{$locus_pos}->{'< 10 years'}++;
            $geno_count->{$study_id}->{$site}->{$marker}->{'< 10 years'}++ if ($mutant_status ne "Wild");          	
        }
        if ($age >= 10) {
            $sample_size->{$study_id}->{$site}->{$locus_name}->{$locus_pos}->{'>= 10 years'}++;
            $geno_count->{$study_id}->{$site}->{$marker}->{'>= 10 years'}++ if ($mutant_status ne "Wild");  
        }	                 
	}	
}

#-----------------------------------------
# parse combination marker data from the
# WWARN database and tabulate sample_size
# + genotyped information
#-----------------------------------------
sub calculate_combination_sample_size_data {
    my ($results, $geno_count, $group_category, $combo_name) = @_;
             
    ## The marker combination names that are parsed in from a tab-delimited text file are labeled as 
    ## marker combination #N as we can have multiple versions of them (i.e. triple mixed #1, triple mixed #2)
    ## we need to drop this numeric to group them all under one category
    $combo_name =~ s/\s+#\d+//;
           
    ## Dealing with combinations of markers is handled slightly 
    ## diffrent in that the results are split into two categories,
    ## by age and by study.
    ##
    ## Tabulating sample size by study is easy enough as the data
    ## returned from the database include the count of genotyped 
    ## marker combinations.
    ##
    ## Tabulating sample size by age requires parsing through the 
    ## data and binning manually.
    ##
    ## Instead of using the markers here all combinations are grouped under
    ## the combination names provided (i.e. double pure, triple mixed, quintuple pure)
    foreach my $row (@$results) {
        my $study_id = $row->[0];
        my $investigator = $row->[1];
        my $country = $row->[2];
        my $site = $row->[3];
        my $markers = $row->[4];
        my $count;
        
        ## Marker combinations need to have the markers that make about the combination stored
        ## for proper prevalance calculations
        $geno_count->{$study_id}->{$site}->{$combo_name}->{'markers'} = $markers unless (exists( $geno_count->{$study_id}->{$site}->{$combo_name}->{'markers'} ));
             
        if ($group_category eq "study") {
            $count = $row->[5];
            
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'genotyped'} = 0 unless (exists( $geno_count->{$study_id}->{$site}->{$combo_name}->{'genotyped'} ));
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'genotyped'} += $count;
        } elsif ($group_category eq "age" && defined($row->[5])) {
        	my $age = $row->[5];
        	
        	## Initialize all our age groups to 0 
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 1 year'} = 0 unless (exists( $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 1 year'} ));
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 5 years'} = 0 unless (exists( $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 5 years'} ));
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 10 years'} = 0 unless (exists( $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 10 years'} ));
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'>= 10 years'} = 0 unless (exists( $geno_count->{$study_id}->{$site}->{$combo_name}->{'>= 10 years'} ));    

            $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 1 year'}++ if ($age < 1);
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 5 years'}++ if ($age < 5);
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'< 10 years'}++ if ($age < 10);
            $geno_count->{$study_id}->{$site}->{$combo_name}->{'>= 10 years'}++ if ($age >= 10);                      
        }
    }    
} 

#-----------------------------------------
# calculate the prevalence data for 
# both single and combination markers 
# grouped by STUDY + SITE and STUDY +
# SITE + AGE GROUP
#-----------------------------------------
sub calculate_prevalence_data {
	my ($sample_size, $total_genotyped) = @_;
	my $prevalence_data = {};
	
	## Calculating prevalance is done by dividing the genotyped data by the sample size,
	## in effect producing the following calculation:
	##
	##     (Genotyped at specific locus name + locus position + SNP value) DIVIDED BY
	##     (Sample size [count] at a specific locus name + locus position)
	##
	## This is further sub-divided into age groups when calculating prevalence by 
	## STUDY + SITE + AGE GROUP
	foreach my $study_id (keys %$total_genotyped) {
		foreach my $site (keys %{ $total_genotyped->{$study_id} }) {
			my $markers = $total_genotyped->{$study_id}->{$site};
			
			## Iterate over each marker/marker combination group and calculate prevalance
			foreach my $marker (sort keys %$markers) {
				$prevalence_data->{$study_id}->{$site}->{'country'} = $sample_size->{$study_id}->{$site}->{'country'} unless ( exists($prevalence_data->{$study_id}->{$site}->{'country'}) );
				$prevalence_data->{$study_id}->{'investigator'} = $sample_size->{$study_id}->{'investigator'} unless ( exists($prevalence_data->{$study_id}->{'investigator'}) );
								
				## First handle grouping by STUDY + SITE
				my $marker_combinations = $markers->{$marker}->{'markers'} if ( exists($markers->{$marker}->{'markers'}) );             
				my $marker_sample_size = _get_marker_sample_size($sample_size, $marker, $study_id, $site, $marker_combinations);
				my $marker_genotyped = $markers->{$marker}->{'genotyped'};
				
				## If we get a count here we want to go ahead and do the calculation otherwise we can
				## enter a prevalence of 0 for this specific marker/marker combination
				if ( defined($marker_genotyped) && exists($marker_sample_size->{'sample_size'}) ) {
					$prevalence_data->{$study_id}->{$site}->{$marker}->{'prevalence'} = ( $marker_genotyped / $marker_sample_size->{'sample_size'});
				} else {
					$prevalence_data->{$study_id}->{$site}->{$marker}->{'prevalence'} = 0;
				}
				
				## Now handle grouping by STUDY + SITE + AGE
				$marker_genotyped = undef;
				foreach my $age_group ("< 1 year", "< 5 years", "< 10 years", ">= 10 years") {
					$marker_genotyped = $markers->{$marker}->{$age_group};
					
					if ( defined($marker_genotyped) && exists($marker_sample_size->{$age_group}) ) {
						$prevalence_data->{$study_id}->{$site}->{$marker}->{$age_group} = ($marker_genotyped / $marker_sample_size->{$age_group});
					} else {
						$prevalence_data->{$study_id}->{$site}->{$marker}->{$age_group} = 0;
					}					
				}				
			}
		}
	}	
	
	return $prevalence_data;
}

#-----------------------------------------
# write both sample size and prevalence
# data to text files and compress into
# tar archive
#-----------------------------------------
sub write_output_tarball {
	my ($sample_size, $prevalence, $tmpdir) = @_;
	
    ## Generate the files we need
    my $sample_size_study = _write_grouped_by_study_output($sample_size, 'sample_size', $tmp_dir);
    my $sample_size_age = _write_grouped_by_age_output($sample_size, 'sample_size', $tmp_dir);
    my $prev_study = _write_grouped_by_study_output($prevalence, 'prevalence', $tmp_dir);
    my $prev_age = _write_grouped_by_age_output($prevalence, 'prevalence', $tmp_dir);
    
    ## Create our tarball file
    chdir($tmp_dir);
    my $tar_outfile = $tmp_dir . "/" . 'wwarn_calculations.tar';
    my $tar = Archive::Tar->new();
    $tar->add_files($sample_size_age, $sample_size_study, $prev_study, $prev_age);
    $tar->write($tar_outfile);
    
    return $tar_outfile;            	  
}

#-----------------------------------------
# writes data binned by age to an output
# file
#-----------------------------------------
sub _write_grouped_by_age_output {
	my ($data, $outfile_type, $tmp_dir) = @_;
	
	## Open file and write header line
	my $outfile = $tmp_dir . "/" . $outfile_type . "_by_age.txt";
	open (AGE_OUT, '>' . $outfile) or $logger->logdie("Could not write to file $outfile: $!");
	print AGE_OUT "#STUDY_ID\tCOUNTRY\tSITE\tINVESTIGATOR\tMARKER\t";
	print AGE_OUT "< 1 year\t< 5 years\t< 10 years\>= 10 years\n";
	
	foreach my $study (keys %$data) {
		foreach my $site (keys %{ $data->{$study} }) {
			next if ($site eq 'investigator');
			my $locus = $data->{$study}->{$site};
			
			foreach my $locus_name (sort keys %$locus) {
				next if ($locus_name eq 'country');
                
                foreach my $position (keys %{ $locus->{$locus_name} }) {
                	my $marker_name = $locus_name . " " . $position;
				    print AGE_OUT "$study\t$data->{$study}->{$site}->{'country'}\t$site\t" .
				                  "$data->{$study}->{'investigator'}\t$marker_name\t" .
				                  "$locus->{$locus_name}->{$position}->{'< 1 year'}\t" .
				                  "$locus->{$locus_name}->{$position}->{'< 5 years'}\t" .
				                  "$locus->{$locus_name}->{$position}->{'< 10 years'}\t" .
				                  "$locus->{$locus_name}->{$position}->{'>= 10 years'}\n";
                }
			}
		}
	}
	
	## Return our filename so we can tar it all together
	close (AGE_OUT);
	return $outfile;
}

#-----------------------------------------
# writes data binned by study to an 
# output file
#-----------------------------------------
sub _write_grouped_by_study_output {
	my ($data, $outfile_type, $tmp_dir) = @_;
	
	my $outfile = $tmp_dir . "/" . $outfile_type . "_by_study.txt";
	open (STUDY_OUT, '>' . $outfile) or $logger->logdie("Could not write to file $outfile: $!");
	print STUDY_OUT "#STUDY_ID\tCOUNTRY\tSITE\tINVESTIGATOR\tMARKER\tucase($outfile_type)\n";
	
	foreach my $study (keys %$data) {
		foreach my $site (keys %{ $data->{$study} }) {
			next if ($site eq 'investigator');
			my $locus = $data->{$study}->{$site};
			
			foreach my $locus_name (sort keys %$locus) {
				next if ($locus_name eq 'country');
				foreach my $position (keys %{ $locus->{$locus_name} }) {
					my $marker_name = $locus_name . " " . $position;
				    print STUDY_OUT "$study\t$data->{$study}->{$site}->{'country'}\t$site\t" .
				                    "$data->{$study}->{'investigator'}\t$marker_name\t" .
				                    "$locus->{$locus_name}->{$position}->{$outfile_type}\n";
				}
			}
		}
	}
	
	close (STUDY_OUT);
	return $outfile;
}

#-----------------------------------------
# given a study ID, site and marker name
# return the count of a marker (locus name,
# locus position, genotype value")
#-----------------------------------------
sub _get_marker_sample_size {
	my ($sample_size, $marker_name, $study, $site, $marker_list) = @_;
	my ($ret_total, $locus_name, $locus_pos, $markers);
	
	## Obtain all locus names and locus positions from the marker name or 
	## from our marker combo lookup table.
    if ($marker_name =~ /(\w+)_(\d+)_(\w+)/) {
    	($locus_name, $locus_pos, undef) = split(/_/, $marker_name);
    	push (@{ $markers }, { 'locus_name' => $locus_name, 'locus_position' => $locus_pos } )
    } elsif ( defined($marker_list) ) {
        my @raw_markers = split(/\s+\+\s+/, $marker_list);
        foreach my $raw_marker (@raw_markers) {
        	($locus_name, $locus_pos) = split(/_/, $raw_marker);
        	push (@{ $markers }, { 'locus_name' => $locus_name, 'locus_position' => $locus_pos } );
        }
    }
    
    ## Iterate over all our markers (if in a combo we do this multiple times) and 
    ## add up the total counts for a specific name/position.
    foreach my $marker (@$markers) {
    	$locus_name = $marker->{'locus_name'};
    	$locus_pos = $marker->{'locus_position'};
    	
    	$ret_total->{'< 1 year'} += $sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'< 1 year'} if ( exists($sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'< 1 year'} ));
    	$ret_total->{'< 5 years'} += $sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'< 5 years'} if ( exists($sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'< 5 years'} ));
    	$ret_total->{'< 10 years'} += $sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'< 10 years'} if ( exists($sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'< 10 years'} ));
    	$ret_total->{'>= 10 years'} += $sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'>= 10 years'} if ( exists($sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'>= 10 years'} ));;
    	
    	$ret_total->{'sample_size'} += $sample_size->{$study}->{$site}->{$locus_name}->{$locus_pos}->{'sample_size'};
    	
    }
    		
	return $ret_total;
}

#-----------------------------------------
# parse haplotype table input to obtain
# all haplotype combinations we want to
# calculate statistics on
#-----------------------------------------
sub _parse_haplotype_table {
	my $haplo_in = shift;
	my $ret_haplo_hash = ();
	
	open (HAPLO, $haplo_in) or $logger->logdie("Could not open haplotype table $haplo_in for parsing: $!");
	while (my $line = <HAPLO>) {
		next if ($line =~ /^#/);
		
		## Our table should contain the following headers:
		## HAPLOTYPE GROUP - HAPLOTYPE NAME - LOCUS NAME - LOCUS POS - GENOTYPE
		chomp ($line);
		my ($haplo_group, $haplo_name, $locus_name, $locus_pos, $genotype) = split(/\t/, $line);
		
		push (@{ $ret_haplo_hash->{$haplo_group}->{$haplo_name} }, $locus_name);
		push (@{ $ret_haplo_hash->{$haplo_group}->{$haplo_name} }, $locus_pos);
		push (@{ $ret_haplo_hash->{$haplo_group}->{$haplo_name} }, $genotype);  
	}
	
	close(HAPLO);
	return $ret_haplo_hash;
}

#-----------------------------------------
# trim whitespace from start and end of
# string
#-----------------------------------------
sub _trim {
    my $string = shift;
    $string =~ s/^\s+//;
    $string =~ s/\s+$//;
    return $string;
}
