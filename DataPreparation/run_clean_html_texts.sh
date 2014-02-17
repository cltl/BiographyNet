
# create provenance information

# get input dir for running program
indir="$1"
logfile="/$indir/log"

# check if log exists and else create it

if [ ! -f $logfile ]; then
touch $logfile
fi


# define namespaces in log (appending in case non-empty log exists)

echo "@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> ." >> $logfile
echo "@prefix prov: <http://www.w3.org/2002/07/prov-o#> ." >> $logfile
echo "@prefix bn: <https://github.com/antske/BiographyNet/> ." >> $logfile
echo "" >> $logfile

# create activity id
me=$(whoami)
my_date=$(date)

act_id="$me${my_date//[[:space:]]/}"
act_id="${act_id/:/}"
act_uri="bn:DataPreparation/clean_html_texts/$act_id" 


# state that data set was made by this activity
echo "bn:$indir" >> $logfile
echo "          a                       prov:Entity ;"  >> $logfile
echo "          prov:wasGeneratedBy     $act_urii ." >> $logfile

# introduce activity
echo "$act_uri" >> $logfile
echo "          a                       prov:Activity ;" >> $logfile
# define software Agent
echo "          prov:wasAssociatedWith  bn:DataPreparation/clean_html_texts.py ;" >> $logfile
# ask for email adres responsible agent
echo "Provide Agent:"
read agent
# TODO: check whether agent is known Agent in BiographyNet domain

echo "          prov:wasAssociatedWith  bn:DataPreparation/clean_html_texts.py ;" >> $logfile
echo "          prov:wasAssociatedWith  bn:$agent ;" >> $logfile

# information about begin time

echo "		prov:startedAtTime	\"$(date)\"^^xsd:dateTime ;" >> $logfile

# run program


echo "		prov:endedAtTime	\"$(date)\"^^xsd:dateTime ." >> $logfile

# data on software agent

pversion=$(python clean_html_texts.py --version)
gversion=$( git rev-parse --verify HEAD)
echo "bn:DataPreparation/clean_html_text.py	bn:version		\"$pversion\"	;" >> $logfile	
echo "					bn:gitVersion		\"$gversion\"	;" >> $logfile	
echo "					prov:wasAssociatedWith	bn:antske	." >> $logfile	

