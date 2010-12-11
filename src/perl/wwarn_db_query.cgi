#!/usr/bin/perl

=head1 NAME

wwarn_db_query.cgi - Retrieves data from the WWARN database in JSON format

=head1 SYNOPSIS

./wwarn_db_query.cgi
	--investigator=<primary investigator name>
	--site=<study site>
	--country=<study country>
	--loc_name=<locus name>
	--loc_pos=<locus position>
	--marker_type=<marker type>
	--genotype_mut_status=<genotype mutant status>
	
=head1 PARAMETERS

B<--investigator, -i>
	Primary Investigator for study (e.x. Price, Sutherland, etc.)

B<--site, -s>
	Study site (e.x. Blantyre, Mae Sot)
	
B<--country, -c>
	Study country (e.x. Thailand, Malawi)
	
B<--loc_name, -n>
	Locus name (e.x. pfcrt, pfdhfr)
	
B<--loc_pos, -p>
	Locus position (For SNP's this should be an integer, for Fragments this should be a decimal)
	
B<--marker_type, -m>
	Either SNP, Copy Number, or Fragment
	
B<--genotype_mut_status, -g>
	Mutant status of genotype - Wild, Mixed, Mutant, No Data
	
=cut

use strict;
use warnings;
use Pod::Usage;	
use DBI;
use CGI qw(:standard);
use JSON;
use Config::IniFiles;	
use Date::Manip qw(ParseDate UnixDate);
use Log::Log4perl qw(:easy);
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);

#-----------------------------------------
# GLOBALS/DEFAULTS
#-----------------------------------------
Log::Log4perl->easy_init( { level => "ALL", file => "/tmp/wwarn_db_query.log" } );
my $logger = get_logger();         
my $start = param("start") || 0;
my $PAGE_SIZE = 25;

my $cfg;
tie %$cfg, 'Config::IniFiles', ( -file => "/export/www/gemina/cgi-bin/wwarn/config/wwarn_db_query.ini" );
my $db_server = $cfg->{'DB'}->{'server'} if ( exists($cfg->{'DB'}->{'server'}) ) || $logger->logdie("Server missing from DB config file.");
my $db_name = $cfg->{'DB'}->{'name'} if ( exists($cfg->{'DB'}->{'name'}) ) || $logger->logdie("DB name missing from DB config file.");
my $username = $cfg->{'DB'}->{'username'} if ( exists($cfg->{'DB'}->{'username'}) ) || $logger->logdie("Username missing from DB config file.");
my $password = $cfg->{'DB'}->{'password'} if ( exists($cfg->{'DB'}->{'password'}) ) || $logger->logdie("Password missing from DB config file.");           

## CGI parameters
my $investigator_name = param("investigator");
my $study_site = param("site");
my $study_country = param("country");
my $locus_name = param("loc_name");
my $locus_position = param("loc_pos");
my $study_group = param("study_group");
my $age = param("age");
my $sample_date = param("sample_date");
my $inclusion_date = param("inclusion_date");
my $marker_value = param("marker_value");
my @marker_type = param("marker_type");
my @mutant_status = param("genotype_mut_stat");
my $download = param("download");

## Open a connection to our database
my $dbh = DBI->connect("DBI:mysql:database=$db_name;host=$db_server", "$username", "$password", 
   		                 { RaiseError => 1, PrintError => 1 }) || $logger->logdie("Could not connect to database $DBI::errstr");

my $results;

my $query = "SELECT s.label, ". 
            "s.investigator, " .
			"l.site, " .
			"l.country, " .
			"sub.patient_id, " .
			"sub.age, " .
			"sub.date_of_inclusion, " .
			"samp.collection_date, " .
			"m.locus_name, " .
			"m.locus_position, " .
			"m.type, " .
			"g.value, " .
			"g.mutant_status " . 
			"FROM study s INNER JOIN location l ON s.id_study = l.fk_study_id " .
			"INNER JOIN subject sub ON s.id_study = sub.fk_study_id " .
			"INNER JOIN sample samp ON sub.id_subject = samp.fk_subject_id " .
			"INNER JOIN genotype g ON samp.id_sample = g.fk_sample_id " .
			"INNER JOIN marker m ON m.id_marker = g.fk_marker_id WHERE";

## Add any parameters if they exist

## Our age needs to be parsed and formatted correctly
if ($age ne "") {
    $query .= parse_age($age);
}

## Both sample date and inclusion date need to be parsed
## and formatted correctly
if ($sample_date ne "") {
    $query .= parse_date($sample_date, "samp.collection_date");
}

## Date of inclusion handled just like our sample date
if ($inclusion_date ne "") {
    $query .= parse_date($inclusion_date, "p.date_of_inclusion");
}

## Also have support for any types of marker values
if ($marker_value ne "") {
    $query .= parse_values($marker_value);
}

$query .= " s.investigator LIKE \"$investigator_name%\" AND" if ( $investigator_name ne "" );
$query .= " s.group = \"$study_group\" AND" if ($study_group ne "");
$query .= " l.country = \"$study_country\" AND" if ( $study_country ne "" );
$query .= " l.site = \"$study_site\" AND" if ( $study_site ne "" );
$query .= " m.locus_name = \"$locus_name\" AND" if ( $locus_name ne "" );
$query .= " m.locus_position = \"$locus_position\" AND" if ( $locus_position ne "" );
$query .= " m.type IN (" . build_sqlin_params(@marker_type) . ") AND" if ( $marker_type[0] ne "" );
$query .= " g.mutant_status IN (" . build_sqlin_params(@mutant_status) . ") AND" if ( $mutant_status[0] ne "" );

$query =~ s/WHERE$//;
$query =~ s/AND$//;

## In order to use our paging we want a count of all rows first
my $sth = $dbh->prepare($query);
$sth->execute();
my $rows = $sth->fetchall_arrayref();

## Execute query...
$query .= " LIMIT $PAGE_SIZE OFFSET $start" if ($download eq "");
$sth = $dbh->prepare($query);
$sth->execute();

$results->{id} = 'wwarn_db_query';
while ( my @raw_results = $sth->fetchrow_array() ) {
	push ( @{ $results->{results} }, 
					{ 
                      'study_label'         => $raw_results[0],
                      'study_investigator' 	=> $raw_results[1], 
					  'study_site'			=> $raw_results[2],
					  'study_country'		=> $raw_results[3],
					  'patient_id'			=> $raw_results[4],
					  'age'					=> format_age($raw_results[5]),
					  'doi'					=> $raw_results[6],
					  'collection_date'		=> $raw_results[7],
					  'locus_name'			=> $raw_results[8],
					  'locus_pos'			=> $raw_results[9],
					  'marker_type'			=> $raw_results[10],
					  'geno_value'			=> $raw_results[11],
					  'geno_status'			=> $raw_results[12]
					}
		 );	 
}

$results->{total} = $#$rows + 1;

## If we have 0 results, then we want to add an empty results array
if ($results->{total} == 0 ) {
    $results->{results} = [];
}

## If the download flag is true we want to write the file to disk
if ($download eq "true") {
    print header(
                    -type => 'application/x-download',
                    -content_encoding => "txt",
                    -attachment => "wwarn_output.txt" );

    print_output_file($results->{results});
} else {
    print header('application/json');
    my $json = new JSON;
    print $json->encode(\%$results);
}

###############################################################################
#####                          SUBROUTINES                                #####
###############################################################################

sub print_output_file {
    my ($results) = @_;

    print  "#STUDY_LABEL\tSTUDY_INVESTIGATOR\tSTUDY_SITE\tSTUDY_COUNTRY\t" .
                    "PATIENT_ID\tAGE\tDATE_OF_INCLUSION\tSAMPLE_COLLECTION_DATE\t" .
                    "LOCUS_NAME\tLOCUS_POSITION\tMARKER_TYPE\tVALUE\tSTATUS\n";

    foreach my $line (@$results) {
        print  "$line->{'study_label'}\t$line->{'study_investigator'}\t$line->{'study_site'}\t" .
                        "$line->{'study_country'}\t$line->{'patient_id'}\t$line->{'age'}\t$line->{'doi'}\t" .
                        "$line->{'collection_date'}\t$line->{'locus_name'}\t$line->{'locus_pos'}\t$line->{'marker_type'}\t" .
                        "$line->{'geno_value'}\t$line->{'geno_status'}\n";
    }
}

sub parse_values { 
    my $values = shift;
    my  $ret_query;

    if ($values =~ /,/) {
        my @values = split(/,/, $values);
        $ret_query = " g.value IN (" . build_sqlin_params(@values) . ") AND";
    } else {
        $ret_query = " g.value = \"$values\" AND";
    }

    return $ret_query;
}

sub parse_age {
    my $age = shift;
    my $ret_query;

    if ($age =~ /^\d$/) {
        $ret_query = " sub.age = $age AND";
    } elsif ($age =~ /(\d+)\s*?\-\s*?(\d+)/) {
        $ret_query = " sub.age BETWEEN $1 AND $2 AND";
    } elsif ($age =~ /^(\<|\>|\<=|\>=)\s*?(\d+)$/) {
        $ret_query = " sub.age $1 $2 AND";
    } elsif ($age =~ /(\<|\>|\<=|\>=)\s*?(\d+)\s*?(\<|\>|\<=|\>=)\s*?(\d+)/) {
        $ret_query = " sub.age $1 $2 AND sub.age $3 $4 AND";
    }

    return $ret_query;
}

sub parse_date {
    my ($raw_date, $field) = @_;
    my $ret_query;

    ## Check if date passed in as mm/dd/yy
    if ($raw_date =~ /^(\d{2})(\/|-)(\d{2})(\/|-)(\d{4})$/) {
        $ret_query = " $field = \"$5-$1-$3\" AND";
    } elsif ($raw_date =~ /(\d{2})(\/|-)(\d{2})(\/|-)(\d{4})\s?-\s?(\d{2})(\/|-)(\d{2})(\/|-)(\d{4})/) {
        $ret_query = " $field >= \"$5-$1-$3\" AND $field <= \"$10-$6-$8\" AND";
    }

    return $ret_query;
}

sub format_age {
	my $age = shift;
	$age =~ s/\.0+$//;
	return $age;
}

sub build_sqlin_params {
	my @params = @_;
	my $query_params;

	foreach my $param (@params) { 
        ## Remove leading or trailing white space
        $param =~ s/(^\s+|\s+$)//;
        $query_params .= "\"$param\",";
    }	
	
    ## Chop off trailing ,
	$query_params =~ s/,$//;

	
	return $query_params;
}
					
