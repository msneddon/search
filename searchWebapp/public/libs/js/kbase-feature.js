/**
 * kbase-feature.js
 * ----------------
 * Javascript for fetching and displaying specific feature information.
 * Similar to the genome info pages, this gets info about features, including
 * name, genome source, strains, regulation, sequence, and so on.
 *
 * It starts by getting the feature ID out of the URL (or as passed programmatically)
 * and uses CDMI.js to get the necessary info.
 */

var genomeURL = "http://140.221.92.12/genome_info/showGenome.html?id=";

var apiURL = "http://www.kbase.us/services/cdmi_api/";
// var proteinInfoURL = "http://140.221.84.191/services/protein_info_service";
//var proteinInfoURL = "http://140.221.84.194:7057";
//var proteinInfoURL = "http://kbase.us/services/protein_info/";
var proteinInfoURL = "http://kbase.us/services/protein_info_service/";
var cdmiAPI = new CDMI_API2(apiURL);
var entityAPI = new CDMI_EntityAPI(apiURL);
var proteinInfoAPI = new ProteinInfo(proteinInfoURL);

var mainFeature;
var featureData;
var mainFid;  // To be populated by various CDMI API calls

// A little div that shows a spinning gif. Doing this early makes it easy to insert/remove from any unfinished div.
var loadingDiv = "<div id=\"loading-image\" align=\"center\"><img src=\"../assets/img/loading.gif\" alt=\"Loading...\"/></div>";

var featureTypes = {
	types : {
		'cds' : 'Coding Sequence',
		'peg' : 'Protein Encoding Gene',
		'opr' : 'Operon',
		'bs'  : 'Binding Site'
	},

	getTypeFromAbbreviation : function(abbrev) {
		if (this.types[abbrev])
			return this.types[abbrev];
		return abbrev.toUpperCase();
	}
};

var loadFeature = function(id) {
	// If nothing passed, get it from the URL
	if (!id)
		id = extractIdFromUrl();

	// If nothing from the URL, throw an error and return
	if (!id) {
		window.alert("Error: No Feature ID found!");
		return;
	}

	// We have an ID here, so load it up.
	populateFeatureInfo(id);
};

/**
 * function: extractIdFromUrl()
 * params:
 *   none
 * returns:
 *   a KBase id extracted from the URL, or undefined if one isn't present.
 * -----------------------------------------------------------------------
 * Extracts the KBase genome id from the current URL, if one's there.
 * It specifically looks for the string: id=kb|g.XXXXXX
 * so that it only gets KBase genome ids.
 */
var extractIdFromUrl = function() {
	var id = location.href.match(/id\=(kb\|.+)\&?/);
	if (id && id.length === 2)
		return(id[1]);
	else
		return '';
};

/**
 * function: populateFeatureInfo(fid)
 * params:
 *   fid = a KBase feature ID string
 * returns:
 *   nothing
 * --------------------------------
 * This function does the heavy lifting of fetching genome feature data from KBase, then
 * sends it along to be visualized.
 */
var populateFeatureEntityInfo = function(feature) {
	mainFeature = feature[mainFid];
	$('#fid').html(mainFid);

	cdmiAPI.fids_to_feature_data([mainFid], populateFeatureDataInfo);
}

//id=kb|g.1104.peg.8434
var populateFeatureDataInfo = function(data) {
	featureData = data[mainFid];
	$('#fun').html(featureData.feature_function);

	// Calculate position across the whole feature - do some wizardry with position and direction.

	var position = "";
	for (var i=0; i<featureData.feature_location.length; i++) {
		if (featureData.feature_location[i][2] === "+") {
			position += featureData.feature_location[i][1] + 
						" - " + 
						(Number(featureData.feature_location[i][1]) + Number(featureData.feature_location[i][3]) - 1) + 
						" (" + featureData.feature_location[i][2] + "),<br/>";
		}
		else {
			position += featureData.feature_location[i][1] + 
						" - " + 
						(Number(featureData.feature_location[i][1]) - Number(featureData.feature_location[i][3]) + 1) + 
						" (" + featureData.feature_location[i][2] + "),<br/>";
		}
	}
	position += "on the contig with KBase id " + featureData.feature_location[0][0];

	$('#pos').html(position);

	var fType = featureTypes.getTypeFromAbbreviation(mainFeature.feature_type.toLowerCase()) + ", ";

	if (featureData.feature_location.length > 1) {
		var chunkLength = 0;
		var startPoint = Number(featureData.feature_location[0][1]);
		var endPoint = Number(featureData.feature_location[0][1]) + Number(featureData.feature_location[0][3]) + 1;

		for (var i=0; i<featureData.feature_location.length; i++) {
			chunkLength += Math.abs(Number(featureData.feature_location[i][3]));
			if (Number(featureData.feature_location[i][1]) < startPoint)
				startPoint = Number(featureData.feature_location[i][1]);
			if (Number(featureData.feature_location[i][1]) + Number(featureData.feature_location[i][3]) + 1 > endPoint)
				endPoint = Number(featureData.feature_location[i][1]) + Number(featureData.feature_location[i][3]) + 1;
		}

		var totalLength = endPoint - startPoint + 1;
		fType += chunkLength + " bp (" + totalLength + " bp total)";
	}
	else {
		fType += featureData.feature_length + " bp";
	}

//	$('#ftype').html(featureTypes.getTypeFromAbbreviation(mainFeature.feature_type.toLowerCase()) + ", " + featureData.feature_length + " bp");
	$('#ftype').html(fType);

	cdmiAPI.fids_to_genomes([mainFid], populateGenomeInfo);
}

var populateGenomeInfo = function(genome) {
	genome = genome[mainFid];
	var source = entityAPI.get_relationship_WasSubmittedBy([genome], [], [], ['id'], 
		// on success
		function(source) {
			$('#org').html("<a href=\"" + genomeURL + genome + "\">" + featureData.genome_name + "</a>");
			$('#source').html(source[0][2]['id'] + ": " + mainFeature.source_id);
		}
	);
}


var populateDNA = function(dnaSeq) {
	dnaSeq = dnaSeq[mainFid];

	$('#dnaSeq').html(formatSequence(dnaSeq));
	$('#gc').html(calculateGCContent(dnaSeq).toFixed(2) + "%");
}

var populateProtein = function(protSeq) {
	$('#protSeq').html(formatSequence(protSeq[mainFid]));
}

var populateOperons = function(operons) {

	operons = operons[mainFid];

	var operonStr = 'No operons found';
	if (operons)
	{
		operonStr = '';
		for (var i in operons)
		{
			operonStr += operons[i] + ' ';
		}
	}
	$('#operon').html(operonStr);
}

var populateDomains = function(domains) {

	domains = domains[mainFid];

	var domList = [];
	for (var dom in domains)
	{
		domList.push(domains[dom]);
	}

	proteinInfoAPI.domains_to_domain_annotations(domList, 
		function(domainAnnotations) {
			var domainStr = 'No domains found';

			if (Object.getOwnPropertyNames(domainAnnotations).length > 0)
			{
				domainStr = '';
				for (var dom in domains)
				{
					domainStr += domains[dom] + ': ' + domainAnnotations[domains[dom]] + '<br />';
				}
			}
			$('#domains').html(domainStr);
		}
	);

}

var populateFamilies = function(families) {
	families = families[mainFid];
	var familyStr = "No protein families found";

	if (families) {
		families = cdmiAPI.protein_families_to_functions(families, 
			// on success
			function(families) {
				var familyStr = '';

				if (families && families.length != 0) {
					for (var fam in families) {
						if (families.hasOwnProperty(fam))
							familyStr += fam + ": " + families[fam] + "<br/>";
					}
				}
				$('#fam').html(familyStr);
			}
		);
	}
	else {
		$('#fam').html(familyStr);
	}
}

var populateRoles = function(roles) {
	roles = roles[mainFid];
	var rolesStr = "No roles found";
	if (roles) {
		rolesStr = roles.join("<br/>");
	}
	$('#roles').html(rolesStr);
}

var populateSubsystems = function(subsystems) {
	subsystems = subsystems[mainFid];
	var subsystemsStr = "No subsystems found";
	if (subsystems) {
		subsystemsStr = subsystems.join("<br/>");
	}
	$('#subsys').html(subsystemsStr);
}

var populateFeatureInfo = function(fid) {
	mainFid = fid;

	entityAPI.get_entity_Feature([fid], ['feature_type', 'function', 'source_id', 'alias'], populateFeatureEntityInfo);
//	feature = feature[fid];

//	cdmiAPI.fids_to_feature_data_async([fid], populateFeatureDataInfo);
//	featureData = featureData[fid];

//	cdmiAPI.fids_to_genomes_async([fid], populateGenomeInfo);
//	genomeId = genomeId[fid];

	proteinInfoAPI.fids_to_domains([fid], populateDomains);
	proteinInfoAPI.fids_to_operons([fid], populateOperons);

	cdmiAPI.fids_to_dna_sequences([fid], populateDNA);
	cdmiAPI.fids_to_protein_sequences([fid], populateProtein);
	/* featureData has fields:
	 * feature_function		- str
	 * feature_id			- str
	 * feature_length		- str (number)
	 * feature_location		- array [contig id, start, strand (+/-), length]
	 * feature_publications	- array
	 */

	/*
	 * stuff I want to get:
	 * name,
	 * organism
	 * genome(s)
	 * strain(s)
	 * GC content
	 * sequence, (nucleic acid, protein)
	 */

	// Starting basic info
//	addTableRow("ID", fid, "featureInfoTable");
//	addTableRow("Organism", featureData.genome_name, "featureInfoTable");
//	addTableRow("Function", featureData.feature_function, "featureInfoTable");
//	addTableRow("Feature type", 
//			featureTypes.getTypeFromAbbreviation(feature.feature_type.toLowerCase()) + 
//			", " + featureData.feature_length + " bp",
//			"featureInfoTable"
//	);
//	var source = entityAPI.get_relationship_WasSubmittedBy([genomeId], [],[],['id']);

//	source = source[0][2]['id'];

//	addTableRow("Source ID", "<b>" + source + ":</b> " + feature.source_id, "featureInfoTable");

	// Sequence info - DNA
//	var dnaSeq = cdmiAPI.fids_to_dna_sequences([fid]);
//	dnaSeq = formatSequence(dnaSeq[fid]);
//	addTableRow("DNA Sequence", dnaSeq, "sequenceTable");

	// Sequence info - Protein
//	var protSeq = cdmiAPI.fids_to_protein_sequences([fid]);
//	protSeq = formatSequence(protSeq[fid]);
//	addTableRow("Protein Sequence", protSeq, "sequenceTable");

//	var position = featureData.feature_location[0][1] + " - " + (Number(featureData.feature_location[0][1]) + Number(featureData.feature_location[0][3])) + " (" + featureData.feature_location[0][2] + ") on contig with KBase id " + featureData.feature_location[0][0];
//	addTableRow("Position", position, "featureInfoTable");

//	var gcContent = calculateGCContent(dnaSeq);
//	addTableRow("GC Content", gcContent.toFixed(2) + "%", "featureInfoTable");

	/**************** Domain and Family info ********************/
	cdmiAPI.fids_to_protein_families([fid], populateFamilies);

	// var families = cdmiAPI.fids_to_protein_families([fid]);
	// families = families[fid];

	// var familyStr = 'No families found';
	// if (families) {
	// 	familyStr = '';
	// 	families = cdmiAPI.protein_families_to_functions(families);

	// 	for (var fam in families) {
	// 		if (families.hasOwnProperty(fam))
	// 			familyStr += fam + ": " + families[fam] + "<br/>";
	// 	}
	// }
	// addTableRow("Protein Families", familyStr, "featureInfoTable");

	cdmiAPI.fids_to_roles([fid], populateRoles);

	// var roles = cdmiAPI.fids_to_roles([fid]);
	// roles = roles[fid];
	// var rolesStr = "No roles found";
	// if (roles) {
	// 	rolesStr = roles.join("<br/>");
	// }
	// addTableRow("Roles", rolesStr, "featureInfoTable");

	cdmiAPI.fids_to_subsystems([fid], populateSubsystems);

	// var subsystems = cdmiAPI.fids_to_subsystems([fid]);
	// subsystems = subsystems[fid];
	// var subsystemsStr = "No subsystems found";
	// if (subsystems) {
	// 	subsystemsStr = subsystems.join("<br/>");
	// }
	// addTableRow("Subsystems", subsystemsStr, "featureInfoTable");
	/*************************************************************/

	/*************** Annotation and Literature References ****************/
	cdmiAPI.fids_to_annotations([fid], populateAnnotations);

	// var annotations = cdmiAPI.fids_to_annotations([fid]);
	// console.log("annotations");
	// console.log(annotations);

	// annotations = processAnnotations(annotations[fid]);
	// addTableRow("Annotations", annotations, "featureInfoTable");

	cdmiAPI.fids_to_literature([fid], populateLiterature);
//	console.log("fid lit");
//	console.log(fidLit);
};

var populateLiterature = function(lit) {
	lit = lit[mainFid];
}

var populateAnnotations = function(annotations) {
//		var annotations = cdmiAPI.fids_to_annotations([fid]);

	annotations = processAnnotations(annotations[mainFid]);
	$('#anno').html(annotations);
//	addTableRow("Annotations", annotations, "featureInfoTable");

}

/**
 * function: processAnnotations
 * params: 
 *   annotations - an Annotations KBase object
 * returns:
 *   a formatted string for all annotations
 */
 var processAnnotations = function(annotations) {
 	if (annotations) {
 		var formatted = [];
 		for (var i=0; i<annotations.length; i++) {

 			formatted.push("<b>annotator:</b> " + annotations[i][1] +
 						 "<br/><b>date:</b> " + new Date(Number(annotations[i][2])*1000).toUTCString() +
 						 "<br/><b>comment:</b> " + annotations[i][0]);
 		}
 		return formatted.join("<br/><br/>");
 	}
 	return "No annotations found";
 };

/**
 * function: calculateGCContent(s)
 * params:
 *   s = the string of interest
 * returns:
 *   the percent of s that consists of G or C
 * ------------------------------------------
 * This calculates the GC content of s, as a percent of the total sequence.
 */
var calculateGCContent = function(s) {
	var gc = 0;
	s = s.toLowerCase();
	for (var i=0; i<s.length; i++) {
		var c = s[i];
		if (c === 'g' || c === 'c') 
			gc++;
	}
	return gc / s.length * 100;
}

/**
 * function: formatSequence(seq)
 * params:
 *   seq = the sequence (DNA, RNA, Protein, etc) to format
 * returns:
 *   a formatted string
 * -------------------------------------------------------
 * This function formats a string (any string, really, but a biological sequence
 * is intended) for showing in the feature browser.
 *
 * Right now, it inserts a <br/> after every 80 characters. A later version might
 * do this formatting in text style, and produce FASTA format or something.
 */
var formatSequence = function(seq) {
	var formatted = '';
	while (seq) {
		formatted += seq.slice(0, 80) + "<br/>";
		seq = seq.slice(80);
	}
	return "<div style='font-family: monospace'>" + formatted + "</div>";
};

/**
 * function: addFeatureTableRow(name, value)
 * params:
 *   name = the name (first element) in the feature table row
 *   value = the value (second element) in the feature table row
 * returns:
 *   nothing
 * -------------------------------------------------------------
 * This adds a new row to the bottom of the feature info table, in the main part of the page.
 */
var addTableRow = function(name, value, tableId) {
	$("#" + tableId).append("<tr><td><strong>" + name + "</strong></td><td>" + value + "</td></tr>");
};

var makeMemoryLink = function(url, id) {
	if (id) 
		url += "?id=" + id;
	return url;
}
