#!/usr/bin/perl

=head1 NAME

wwarn_convert_to_mysql.cgi - CGI scripts that converts the WWARN template format to a MySQL ready format

=head1 SYNOPSIS

./transform_WWARN_input.pl 
        [--input_data_file=/path/to/input/file]
        
=head1 PARAMETERS

B<--input_data_file, -i>
    The input data files that should be transformed. This file should be a tab delimited
    text file.
    
=head1 DESCRIPTION            

This CGI script takes a WWARN template formated tab-delimited file and parses out the relevant data
to produce text files that map to the WWARN database tables (study, location, subject, sample, marker, genotype).
These text files are ready to be loaded into their respective tables.

=head1 INPUT

An input tab-delimited file conforming to the template created for WWARN submissions. In conjunction
with a mutant status key valid SQL files for each table in the WWARN DB (study, marker, subject, sample)
should be generated.

=head1 OUTPUT

A set of six text files, study.txt - location.txt - subject.txt - sample.txt - marker.txt - genotype.txt, which
contain the parsed data in a MySQL ready format.

=head1 CONTACT

    Cesar Arze
    carze@som.umaryland.edu

=cut

use strict;
use warnings;
use FileHandle;
use File::Basename;
use Pod::Usage;		
use DBI;
use CGI qw(:standard);
use JSON;
use URI::Escape;
use Config::IniFiles;	
use Log::Log4perl qw(:easy);

#----------------------------------------------------------
# GLOBALS/COMMAND-LINE OPTIONS
#----------------------------------------------------------
$CGI::POST_MAX = 1024 * 10000;

my $logger;
my $cfg;
my $dbh;
my $mutant_status_lookup;
my $LOG;
my $json = new JSON;
my $query = new CGI;

Log::Log4perl->easy_init( { level => "ALL", file => "/tmp/wwarn_mysql.log" } );
$logger = get_logger();                    

#$my $input_file = &save_local_template_file( $query->param("input_data_file"), $query->upload("input_data_file") );
my $input_file = param('input_data_file');

## Stores max ID's for each table
my $MAX_IDS = { "study"     => 1,
				"location"	=> 1,
                "sample"    => 1,
                "subject"   => 1,
                "genotype"  => 1,
                "marker"    => 1 };

my $OUT_FILES = ();                  
my $CODON_LOOKUP = ();                    
my $MUTANT_STATUS = ();                
my $SQL = ();

my $new_studies = ();
my $new_locations = ();
my $new_subjects = ();
my $new_samples = ();
my $new_genotypes = ();
my $new_markers = ();

my $cfg_file = "/export/co/wwarn/conf/wwarn.ini";
tie %$cfg, 'Config::IniFiles', ( -file => $cfg_file );
my $db_server = $cfg->{'DB'}->{'hostname'} if ( exists($cfg->{'DB'}->{'hostname'}) ) || _log_errors("Server missing from DB config file.");
my $db_name = $cfg->{'DB'}->{'database_name'} if ( exists($cfg->{'DB'}->{'database_name'}) ) || _log_errors("DB name missing from DB config file.");
my $username = $cfg->{'DB'}->{'username'} if ( exists($cfg->{'DB'}->{'username'}) ) || _log_errors("Username missing from DB config file.");
my $password = $cfg->{'DB'}->{'password'} if ( exists($cfg->{'DB'}->{'password'}) ) || _log_errors("Password missing from DB config file.");
my $mutant_status = $cfg->{'GENERAL'}->{'mutant_status'} if ( exists($cfg->{'GENERAL'}->{'mutant_status'}) ) || 
                        _log_errors("Mutant status file missing from config file.");
my $output_dir = $cfg->{'GENERAL'}->{'output_directory'} if ( exists($cfg->{'GENERAL'}->{'output_directory'}) ) || 
                        _log_errors("Output directory missing from config file.");

$CODON_LOOKUP = $cfg->{'CODON'};
$OUT_FILES = $cfg->{'FILES'};
$MUTANT_STATUS = $cfg->{'MUTANT_STATUS'};
$SQL = $cfg->{'SQL'};

print header("text/html");

my $out_file_prefix = basename($input_file, (".txt", ".TXT"));

$dbh = DBI->connect("DBI:mysql:database=$db_name;host=$db_server", "$username", "$password", 
                    { RaiseError => 1, PrintError => 1 }) || _log_errors("Could not connect to database $DBI::errstr");

$MAX_IDS = &get_max_ids($MAX_IDS);

$mutant_status_lookup = &parse_mutant_status_key($mutant_status);
my $formatted_data = &parse_input_file($input_file);

my $FOUT = &open_files($output_dir, $OUT_FILES);

my $study_row_count = print_sql_file($FOUT->{"study"}, $new_studies);
my $location_row_count = print_sql_file($FOUT->{"location"}, $new_locations);
my $subject_row_count = print_sql_file($FOUT->{"subject"}, $new_subjects);
my $sample_row_count = print_sql_file($FOUT->{"sample"}, $new_samples);
my $marker_row_count = print_sql_file($FOUT->{"marker"}, $new_markers);
my $genotype_row_count = print_sql_file($FOUT->{"genotype"}, $new_genotypes);

$LOG->{'success'} = JSON::true;

unshift(@{ $LOG->{'results'} }, { 'wwarn_logmsg' => "Number of markers to be added: $marker_row_count" } );
unshift(@{ $LOG->{'results'} }, { 'wwarn_logmsg' => "Number of genotypes to be added: $genotype_row_count" } );
unshift(@{ $LOG->{'results'} }, { 'wwarn_logmsg' => "Number of samples to be added: $sample_row_count" } );
unshift(@{ $LOG->{'results'} }, { 'wwarn_logmsg' => "Number of sujbects to be added: $subject_row_count" } );
unshift(@{ $LOG->{'results'} }, { 'wwarn_logmsg' => "Number of locations to be added: $location_row_count" } );
unshift(@{ $LOG->{'results'} }, { 'wwarn_logmsg' => "Number of studies to be added: $study_row_count" } );

print $json->encode(\%$LOG);

###############################################################################
#####                          SUBROUTINES                                #####
###############################################################################

#----------------------------------------------------------
# print output files
#----------------------------------------------------------
sub print_sql_file {
    my ($out_file, $data) = @_;
    my $row_count = 0;

	foreach my $key ( sort { $data->{$a} <=> $data->{$b} } keys %$data) {
		print $out_file join( "\t", ( $data->{$key}, split($;,$key) )  ) . "\n";
        $row_count++;
	}
	    
    return $row_count;
}

#----------------------------------------------------------
# parse input data file
#----------------------------------------------------------
sub parse_input_file {
    my ($data_file, $map_file) = @_;
    my $marker_key = ();
    my $genotypes_added;
    $logger->info("** In parse_input_file **");
       
    open (INDATA, $data_file) or _log_errors("Could not open input data file $data_file: $!");
    while (my $row = <INDATA>) {
        next if $row =~ /^\n/;
        chomp ($row);
        
        my @fields = map( trim($_), split(/\t/, $row) );

        if ($row =~ /^#/) {
            $row =~ s/\t+$//;
            $marker_key = &parse_markers_from_header(@fields) unless ($#fields < 9);
            next;
        }

        ## We want to make sure that we have marker data for this row before we do 
        ## any extra processing.
        if ($#fields < 9) {
            $logger->warn("Row has no marker data: $row");
            next;
        }
        
        my $wwarn_study_id = $fields[0];
        my $investigator = $fields[1];
        my $study_label = $fields[2];
        my $country = $fields[3];
        my $site = $fields[4];
        my $patient_id = $fields[5];
        my $age = $fields[6];
        my $doi = $fields[7];
        my $sample_date = $fields[8];        
                 
		## If age is empty we want to set it to null
		$age = "\\N" if ( ($age eq "") || ($age eq "NODATA") );
         
        my $db_study_id = &pull_or_create_new_study_db_id($row, $wwarn_study_id, $investigator, $study_label);
        my $db_location_id = &pull_or_create_new_location_db_id($row, $db_study_id,$country, $site);
        my $db_subject_id = &pull_or_create_new_subject_db_id($row, $db_study_id, $db_location_id, $patient_id, $age, $doi);
        my $db_sample_id = &pull_or_create_new_sample_db_id($row, $db_subject_id, $sample_date);
        
        ## Parse marker data
        for (my $i = 9; $i <= $#fields; $i++) {
            unless ( ($fields[$i]) ne "" ) {
                next;
            } 

            my $marker_info = $marker_key->{$i};
            my $locus_name = $marker_info->{'name'};
            my $locus_position = $marker_info->{'position'};


            my $marker_type = $marker_info->{'type'};
            my $molecule_type = $marker_info->{'molecule_type'};
            my $value = $fields[$i];
            my $mutant_status;
            
            unless ( defined($molecule_type) ) {
                $molecule_type = "";
            }

            ## If we are working with copy number our position will be set to NULL
            $locus_position = "\\N" if ($marker_type eq "Copy Number");
            
            ## If our genotype value is Not genotyped, Genotyping failure or "" we want to 
            ## set our molecule_type to an empty string (This is really messy)
            if ( lc($value) =~ /not genotyped|genotyping failure/ ) {
                $molecule_type = ""
            }

            ## If our marker type is SNP we can pull down a mutant status.
            if ($marker_type eq "SNP") {
            	$mutant_status = $mutant_status_lookup->{$locus_name}->{$locus_position}->{$value};
            	
            	## For any mixed data types we should check both combinations, A/B and B/A to see if they are in our lookup table
            	if ($value =~ /(\w)\/(\w)/) {
            		my $switched_value = "$2/$1";
            		$mutant_status = $mutant_status_lookup->{$locus_name}->{$locus_position}->{$switched_value} unless ( defined($mutant_status) );
            	}             
            }
            
            $mutant_status = "No Data" unless ( defined($mutant_status ) );     
            
            my $db_marker_id = &pull_or_create_new_marker_db_id($row, $locus_name, $locus_position, $marker_type);
            my $db_genotype_id = &pull_or_create_new_genotype_db_id($row, $db_sample_id, $db_marker_id, $value, $mutant_status, $molecule_type);
   
            next unless ( defined($db_genotype_id) );
 
            $new_genotypes->{$db_sample_id, $db_marker_id, $value, $mutant_status, $molecule_type} = $db_genotype_id if ($db_genotype_id == ($MAX_IDS->{"genotype"} - 1));
        }

        $new_studies->{$wwarn_study_id, $investigator, $study_label} = $db_study_id;
        $new_locations->{$db_study_id, $country, $site} = $db_location_id;
        $new_subjects->{$db_study_id, $db_location_id, $patient_id, $age, $doi} = $db_subject_id;
        $new_samples->{$db_subject_id, $sample_date} = $db_sample_id;
    }
    
    close (INDATA);
}

#----------------------------------------------------------
# obtain or create db id from genotype table/hash
#----------------------------------------------------------
sub pull_or_create_new_genotype_db_id {
    my ($row_line, $sample_id, $marker_id, $val, $status, $mol_type) = @_;
    my $db_id;
    $logger->info("** In create_new_genotype_row **");
    
    ## Check for duplicate row
    if ( defined($new_genotypes->{$sample_id, $marker_id, $val, $status, $mol_type}) ) {
        $logger->warn("Duplicate genotype skipping the following row: $row_line");
    } else {
        $db_id = &get_table_id_from_db('genotype', $sample_id, $marker_id, $val, $status, $mol_type);
        
        unless ( defined($db_id) ) {
            $db_id = get_new_table_id('genotype')
        }

        ## If our db_id does not equal our $MAX_IDS->{'genotype'} - 1 we know we have a
        ## duplicate row here
        unless ($db_id == ($MAX_IDS->{'genotype'} - 1)) {
            $logger->warn("Duplicate genotype skipping the following row: $row_line");
            $db_id = undef;            
        }
    }
    
    return $db_id;
}

#----------------------------------------------------------
# obtain or create db id from marker table/hash
#----------------------------------------------------------
sub pull_or_create_new_marker_db_id {
    my ($row_line, $name, $position, $type) = @_;
    my $db_id;
    $logger->info("** In create_new_marker_row **");
    
    ## Check for duplicate row
    if ( defined($new_markers->{$name, $position, $type}) ) {
        $logger->warn("Duplicate marker row: $row_line");
        $db_id = $new_markers->{$name, $position, $type};
    } else {
        $db_id = &get_table_id_from_db('marker', $name, $position, $type);

        # If our db_id here is undefined we know that this is a new marker
        # and should add it to our new_markers hash
        unless ( defined($db_id) ) {
            $db_id = $MAX_IDS->{'marker'};   
            $MAX_IDS->{'marker'}++;
            $new_markers->{$name, $position, $type} = $db_id
        }
    }
    
    return $db_id;
}

#----------------------------------------------------------
# add a row to the sample table hash
#----------------------------------------------------------
sub pull_or_create_new_sample_db_id {
    my ($row_line, $subject_id, $collection_date) = @_;
    my $db_id;
    $logger->info("** In create_new_sample_row **");
    
    ## Verify that we do not have a duplicate row here
    if ( defined($new_samples->{$subject_id, $collection_date}) ) {
        $logger->warn("Duplicate sample row: $row_line");
        $db_id = $new_samples->{$subject_id, $collection_date};
    } else {
        $db_id = &get_table_id_from_db('sample', $subject_id, $collection_date);
        
        unless ( defined($db_id) ) {
            $db_id = get_new_table_id('sample')
        }
    }
    
    return $db_id;
}

#----------------------------------------------------------
# add a row to the subject table hash
#----------------------------------------------------------
sub pull_or_create_new_subject_db_id {
    my ($row_line, $study_id, $location_id, $patient_id, $age, $doi) = @_;
    my $db_id;
    $logger->info("** In create_new_subject_row **");
    
    ## Verify that we do not have a duplicate row here
    if ( defined($new_subjects->{$study_id, $location_id, $patient_id, $age, $doi}) ) {
        $logger->warn("Duplicate subject row: $row_line");
        $db_id = $new_subjects->{$study_id, $location_id, $patient_id, $age, $doi};
    } else {
        $db_id = &get_table_id_from_db('subject', $study_id, $location_id, $patient_id, $age, $doi);  

        unless ( defined($db_id) ) {
            $db_id = get_new_table_id('subject')
        }
    }
    
    return $db_id;
}

#----------------------------------------------------------
# add a row to the locations table hash
#----------------------------------------------------------
sub pull_or_create_new_location_db_id {
    my ($row_line, $study_id, $country, $site) = @_;
    my $db_id;
    $logger->info("** In create_new_location_row **");
    
    ## Verify that we do not have a duplicate row here
    if ( defined($new_locations->{$study_id, $country, $site}) ) {
        $logger->warn("Duplicate location row: $row_line");
        $db_id = $new_locations->{$study_id, $country, $site};    
    } else {
        $db_id = &get_table_id_from_db('location', $study_id, $country, $site);         
        
        unless ( defined($db_id) ) {
            $db_id = get_new_table_id('location')
        }
    }

    return $db_id;
}


#----------------------------------------------------------
# add a row to the studies table hash
#----------------------------------------------------------
sub pull_or_create_new_study_db_id {
    my ($row_line, $study_id, $investigator, $label) = @_;
    my $db_id;
    $logger->info("** In create_new_study_row **");
    
    ## Verify that we do not have a duplicate row here
    if ( defined($new_studies->{$study_id, $investigator, $label}) ) {
        $logger->warn("Duplicate study row: $row_line");
        $db_id = $new_studies->{$study_id, $investigator, $label};    
    } else {
        $db_id = &get_table_id_from_db('study', $study_id, $investigator, $label);          

        unless ( defined($db_id) ) {
            $db_id = get_new_table_id('study')
        }

    }

    return $db_id;
}

#----------------------------------------------------------
# lookup the primary key for one of the WWARN tables
#----------------------------------------------------------
sub get_table_id_from_db {
    my $table = shift;
    my @params = @_;
    my $id;
    
    eval {
        my $sth = $dbh->prepare($SQL->{$table});
        $sth->execute(@params);
        $id = $sth->fetchrow_array();
    };
    _log_errors("Could not retrieve primary key from table $table: $@") if ($@);
    
    
    return $id;
}

sub get_new_table_id {
    my $table = shift;
    my $new_id = $MAX_IDS->{$table};
    $MAX_IDS->{$table}++;

    return $new_id;
}

#----------------------------------------------------------
# parser marker information header line
#----------------------------------------------------------
sub parse_markers_from_header {
    my @header = @_;
    my $marker_key;
    $logger->info("** Parsing marker header line **");
    
    ## We start with the 7th element because this should be where markers begin.
    ## Loop through the elements in the header and capture the locus name,
    ## locus type and locus position (if it exists)
    for (my $i = 9; $i < scalar (@header); $i++) {
        my $marker_header = $header[$i];
        next if ($marker_header eq ""); ## Excel adds a trailing tab to the header line

        ## The marker column header should be of the following format:
        ##
        ##          <LOCUS_NAME>_<LOCUS_POSITION *OPTIONAL*>_<LOCUS_TYPE>_<MOLECULE_TYPE *OPTIONAL*>
        ## 
        ## We need to check the type first to determine what processing will
        ## be done
        my @elements = split(/_/, $marker_header);

        ## Based off the size of our array we can tell what kind of marker this is:
        ##      Size = 2 --> pfmdr1_CN       
        ##      Size = 4 --> pfcrt_76_SNP_AA (SNP with molecule type defined)

        if ( scalar(@elements) == 2 ) {
            my $raw_marker_type = lc($elements[-1]);
            my $marker_type = "";
            
            ## Dealing with either a copy number of fragment here, check to see what we have
            if      ($raw_marker_type eq "cn")   { $marker_type = "Copy Number"  }
            elsif   ($raw_marker_type eq "frag") { $marker_type = "Fragment"     }
            else                                 { _log_errors("ERROR: Header " . join(" - ", @header) . "contains a malformed marker ($marker_header) type - $marker_type");
                                                   next;                         }

            $marker_key->{$i} = { 'name' => $elements[0], 'type' => $marker_type };            
        } elsif ( scalar(@elements) == 4 ) {
            ## SNP with molecule type
            my $raw_molecule_type = lc( $elements[-1] );
            my $molecule_type = "";

            if      ($raw_molecule_type eq "aa") { $molecule_type = "Amino Acid"; }
            elsif   ($raw_molecule_type eq "nt") { $molecule_type = "Nucleotide"; }
            else                                 { _log_error("ERROR: Header " . join(" - ", @header) . "contains a malformed molecule type ($raw_molecule_type)");
                                                   next;                          }

            $marker_key->{$i} = { 'name' => $elements[0], 'type' => 'SNP', 'position' => $elements[1], 'molecule_type' => $molecule_type };            
        } else {
            # Don't know what we are dealing with here so just flag it as an error
            _log_errors("ERROR: Header " . join(" - ", @header) . "contains a malformed marker ($marker_header)");
        }         
    }
    
    return $marker_key;
}

#----------------------------------------------------------
# parser marker information header line
#----------------------------------------------------------
sub parse_mutant_status_key {
    my $mutant_status_file = shift;
    my $mutant_key = ();
    $logger->info("** Parsing mutant status key **");
    
    open (MUTANT, $mutant_status_file) or _log_errors("Could not open mutant status $mutant_status_file: $!");
    while (my $line = <MUTANT>) {
        chomp ($line);
        
        ## The file should be a tab-delimited file with four columns:
        ##
        ##      locus name\tlocus position\tcodon\tmutant status
        ##
        my ($name, $position, $codon, $status) = split(/\t/, $line);
        
        ## Want to make sure that our locus position, 
        ## codon and mutant status are all well formed.
        next if ( &verify_position($line, $position) );
        next if ( &verify_codon($line, $codon) );
        next if ( &verify_mutant_status($line, $status) );
        
        $mutant_key->{$name}->{$position}->{$codon} = $status;        
    }    
    
    close (MUTANT);
    return $mutant_key;
}

#----------------------------------------------------------
# verify that mutant status is well-formed
#----------------------------------------------------------
sub verify_mutant_status {
    my ($line, $status) = @_;
    my $ret = 0;
    
    unless ( exists( $MUTANT_STATUS->{$status} ) ) {
        $logger->warn("WARN: $line contains a malformed mutant status - $status");
        $ret = 1;
    }
    
    return $ret;
}

#----------------------------------------------------------
# verify that mutant status codon is well-formed
#----------------------------------------------------------
sub verify_codon {
    my ($line, $codon_str) = @_;
    my @codons = ();
    my $ret = 0;
    
    ## Codons can also come in the format of <CODON1>/<CODON2>
    if ($codon_str =~ /\w\/\w/) {
        @codons = split(/\//, $codon_str);
    } else {
        push (@codons, $codon_str);
    }
    
    ## Check each codon to make sure it is a valid codon
    foreach my $codon (@codons) {
        unless ( exists($CODON_LOOKUP->{$codon} ) ) {
            $logger->warn("WARN: $line contains a malformed codon value - $codon_str");
            $ret = 1;
            last;
        }
    }
    
    return $ret;
}

#----------------------------------------------------------
# verify that mutant status table position is well-formed
#----------------------------------------------------------
sub verify_position {
    my ($line, $pos) = @_;
    my $ret = 0;
    
    if ($pos !~ /\d+/) {
        $logger->warn("WARN: $line contains a malformed position - $pos");
        $ret = 1;
    }
    
    return $ret;
}

#----------------------------------------------------------
# get max ids for all tables in WWARN db
#----------------------------------------------------------
sub get_max_ids {
    my $ids = shift;
    my $sth;
            
    foreach my $table (keys %$ids) {
        $sth = $dbh->prepare("SELECT MAX(id_$table) FROM " . $dbh->quote_identifier($table) );
        $sth->execute();
        my $id = $sth->fetchrow_array();
        
        if ( defined($id) ) {
            $ids->{$table} = ++$id;
        } else {
            $ids->{$table} = 1;
        }
    }    
    
    return $ids;
}

#----------------------------------------------------------
# open all output files
#----------------------------------------------------------
sub open_files {
    my ($out_dir, $files) = @_;
    my $open_files = ();
    my $fh; 
    
    foreach my $table (keys %$files) {
        my $out_file = $out_dir . "/" . $out_file_prefix . $files->{$table};
        $fh = FileHandle->new($out_file, "w");
        $open_files->{$table} = $fh;                
    }
    
    return $open_files;
}

#----------------------------------------------------------
# trim white space from beginning/end of string
#----------------------------------------------------------
sub trim {
	my $string = shift;
	$string =~ s/^\s+//;
	$string =~ s/\s+$//;
	return $string;
   
}

#----------------------------------------------------------
# saves the passed in template file to local disk to be
# processed by the rest of the script.
#----------------------------------------------------------
sub save_local_template_file {
    my ($filename, $filehandle) = @_;
    my $local_file = "/tmp/$filename";
    
    ## If our filesize was over 10MB then we won't have a filename here and we can return a message error
    _log_errors("Files over 10MB are not supported. Please split file and re-try") unless ($filename);

    open(UPLOADFILE, ">$local_file") or _log_errors("Could not write to local file /tmp/$filename");
    binmode UPLOADFILE;

    while (<$filehandle>) { print UPLOADFILE; }
    close UPLOADFILE;

    return $local_file;
}

#----------------------------------------------------------
# Writes out fatal errors to both a JSON object and 
# the logger.
#----------------------------------------------------------
sub _log_errors {
    my $err_msg = shift;
    my $json_err;

    $json_err = { 'success' => JSON::false, 'msg' => uri_escape($err_msg), 'results' => [] };
    print $json->encode(\%$json_err);
    $logger->logdie($err_msg);
}

