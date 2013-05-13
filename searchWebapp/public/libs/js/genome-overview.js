/**
 * kbase-genome-info-widget.js
 * ---------------------------
 * This Javascript file contains functions to fetch and draw information about
 * a single KBase genome.
 *
 * Currently (as of 10/12/2012), it does all its work client-side, which can kinda beat the tar
 * out of a machine that doesn't have a whole lot of RAM. Sooner or later, much of this will
 * move server-side.
 *
 * It mostly works by chaining together a series of asynchronous CDMI API calls. Starting with 
 * a given genome ID in the URL, it fetches much of the information that is present, including 
 * contig and feature info.
 *
 * To get the ID from the URL, it searches for the pattern "id=kb|g.xxxx" (a KBase genome id). 
 * Any other parameter is ignored.
 *
 * Bill Riehl
 * wjriehl@lbl.gov
 * Lawrence Berkeley National Lab
 * 10/12/2012
 */

//var featureURL = "http://140.221.92.12/feature_info/feature.html?id=";
var featureURL = "/services/search/details/";

// Initialize CDMI API object
var apiURL = "http://www.kbase.us/services/cdmi_api/";
var cdmiAPI = new CDMI_API2(apiURL);
var entityAPI = new CDMI_EntityAPI(apiURL);

var contigWidget;

var numLoading = 0;			// This tracks the number of currently unfinished asynchronous calls (some of which may be parallel)
							// I bet there's a better way to do this, but I haven't figured it out yet...
var svgWidth = 500;			// width of Feature widget SVG
var svgHeight = 500;		// height of Feature widget SVG
var bpPerPixel = 10;

var genome;						// genome of interest
var target;					// target DOM id
var fids;					// array of feature ids
var fid2FeatureData;		// hash of features (by feature id)
var contigs;				// list of contig ids associated with the given genome
var fid2Subsystems;			// hash of subsystems by feature id
var featureTypes;			// associative array of featureTypes. featureTypes[type] = index (for placing features by type)

// Flags to tell whether each view has been fully constructed.
var contigViewMade = false;
var gcContentViewMade = false;
var taxonomyViewMade = false;

// A little div that shows a spinning gif. Doing this early makes it easy to insert/remove from any unfinished div.
var loadingDiv = "<div id=\"loading-image\" align=\"center\"><img src=\"/services/search/libs/imgs/loader.gif\" alt=\"Loading...\"/></div>";

// A generic color list from d3.
var colorList = d3.scale.category20c();

// A dummy button that might be used for adding some bit of information ot the workflow.
// Currently it does nothing, but it looks important!
var toWorkflowButton = "<a href=\"#\" class=\"btn btn-primary\">Add to Workflow</a>";

/**
 * function: getGenome(id)
 * params:
 *   id = a KBase id string
 * returns:
 *   nothing
 * ------------------------
 * This is the entry class to the genome info widget.
 * If id is given, then use it to look up all the genome info we can find.
 * If it NOT given, then try to extract it from the URL.
 * If it's still not there, then we have a problem and should stop and alert the user.
 *
 * Once we have a valid-looking genome id, pass it to populateGenome() and continue.
 */
var getGenome = function(id) {
	// if id = null, extract from html
	// if html is null (or the id field isn't present in the url), then god help you.

	if (!id) {
		id = extractIdFromLocation();
	}

	if (!id) { // STILL undefined
		window.alert("Unable to retrieve genome ID!");
		// do something to catch it and return.
		return;
	}

	$("#contigMenuContainer").html(loadingDiv);
	$("#contigWidgetContainer").html(loadingDiv);
	populateGenome(id);
};

/**
 * function: populateContigs(contig_data)
 * params:
 *   contigData = an object returned from CDMI.genomes_to_contigs
 * returns:
 *   nothing
 * -------------------------------------------------------------
 * This simply passes the command along to find the lengths of all contigs via 
 * an asynchronous CDMI call, and responds to that call.
 *
 * contig_data is expected to be the object resulting from the CDMI call to
 * genomes_to_contigs()
 */
var populateContigs = function(contigData) {
	cdmiAPI.contigs_to_lengths(contigData[genome.id], populateContigLengthsAndBrowser);

};

/**
 * function: populateContigLengths(contig_lengths)
 * params:
 *   contigLengths = an object returned from CDMI.contigs_to_lengths
 * returns:
 *   nothing
 * ------------------------------------------------------------------
 * This associates all contig lengths with a contig, and sets up space for all of its
 * feature info (if not present already).
 * 
 * It then follows it up with a call to populateData().
 */
var populateContigLengthsAndBrowser = function(contigLengths) {
	contigs = contigLengths;
	for (contig in contigs) {
		var len = contigs[contig];
		contigs[contig] = {
							"length": len,
							"features": {},
							"numFeatures": 0
						  };
	}
	
	// put contig info into a list of tuples
	var contigTuples = [];
	for (var contig in contigs)
		contigTuples.push([contig, contigs[contig].length]);

	// sort that list of tuples
	contigTuples.sort(function(a, b) {
		return b[1] - a[1];
	});

	makeContigDropdown(contigTuples, 'contigMenu', '#contigMenuContainer', 'showContig()');
	makeContigDropdown(contigTuples, 'gcMenu', '#gcMenuContainer', 'showGCContent()');

	// Finally, given the genome info and page target, get all the data needed.
	contigWidget = makeContigWidget("contigTrackContainer", 700, 100, {"contig": contigTuples[0][0],
																	   "onClickFunction": selectHighlight,
																	   "allowResize": true });

	$('#contigButtonContainer').html("<div class='btn-group' style=''><button class='btn btn btn-info btn-small'  onClick=\"contigWidget.moveLeftEnd();\"><i class='icon-step-backward icon-white'></i> First</button>\n" + 
            						 "<button class='btn btn btn-info btn-small'  onClick=\"contigWidget.moveLeftStep();\"><i class='icon-chevron-left icon-white'></i> Previous</button>\n" +
            						 "<button class='btn btn btn-info btn-small'  onClick=\"contigWidget.zoomIn();\"><i class='icon-plus-sign icon-white'></i> Zoom In</button>\n" +
            						 "<button class='btn btn btn-info btn-small'  onClick=\"contigWidget.zoomOut();\"><i class='icon-minus-sign icon-white'></i> Zoom Out</button>\n" +
            						 "<button class='btn btn btn-info btn-small'  onClick=\"contigWidget.moveRightStep();\"><i class='icon-chevron-right icon-white'></i> Next</button>\n" +
						             "<button class='btn btn btn-info btn-small'  onClick=\"contigWidget.moveRightEnd();\"><i class='icon-step-forward icon-white'></i> Last</button>\n</div>");

//	contigWidget.init();
};

/**
 * function: populateGenome(id)
 * params:
 *   id = The KBase id of a genome of interest.
 * returns:
 *   nothing
 * ----------------------------
 * This populates the genome information page with KBase info from the given genome id.
 * It fetches the genome entity information (not asynchronously, but fast enough it shouldn't matter. Shouldn't...)
 * and uses that to populate a list of static fields.
 * 
 * It then uses the genome id to start the chain of asynchronous CDMI API calls used to build the feature info
 * browser.
 */
var populateGenome = function populateGenome(id) {
	genome = entityAPI.get_entity_Genome([id], 
								['id', 'contigs'], doGenomePopulation);
	/*
	genome = entityAPI.get_entity_Genome([id], 
								['id', 'scientific_name', 'domain', 'complete', 
								 'dna_size', 'source_id', 'contigs', 'gc_content', 
								 'source_id', 'pegs', 'rnas'], doGenomePopulation);
								 */
};

var doGenomePopulation = function(returnedGenome) {
	// There's only one Genome we care about here - the one with the id as given.
	// This is an object with properties with names as given in the list of fields above.
	for (id in returnedGenome) {
		genome = returnedGenome[id];
	}

	/*
	// Fetch the list of feature ids and taxonomy chain.
	var taxonomy = cdmiAPI.genomes_to_taxonomies([genome.id], populateTaxonomy);
	var fids = cdmiAPI.genomes_to_fids([genome.id], [], populateFeatureIds);

	// Write all the static fields in order based on the fetched genome information.
	$('#gID').html(genome.id);
	$('#gName').html(genome.scientific_name);
	$('#genomename').html(genome.scientific_name);
	$('#gDomain').html(genome.domain);
	$('#gComp').html(genome.complete==="1" ? "Yes" : "No");
	$('#gDNA').html(numberFormatComma(genome.dna_size) + " bp");
	$('#gGC').html(Number(genome.gc_content).toFixed(2) + "%");
	$('#gContigs').html(genome.contigs);
	$('#gPegs').html(genome.pegs);
	$('#gRNAs').html(genome.rnas);

	entityAPI.get_relationship_WasSubmittedBy([genome.id], [], [], ['id'], populateSource);

	$('#gSource').html(genome.source_id);
	*/

	cdmiAPI.genomes_to_contigs([genome.id], populateContigs);
};

var populateSource = function(source) {
	$('#gSource').html(source[0][2]['id'] + ": " + genome.source_id);
}

var populateTaxonomy = function(taxonomy) {
	// Combine the taxonomy array into a hierarchy that makes it visible at a glance.
	// Essentially, add a <br/> and extra spaces to the front of each element
	// so
	//   that
	//     it
	//       looks
	//         like
	//           this.
	taxonomy = taxonomy[genome.id];
	var taxString = "No taxonomy found";
	if (taxonomy !== undefined && taxonomy.length > 0) {
		var taxString = taxonomy[0];
		for (var i=1; i<taxonomy.length-1; i++) {
			taxString += "<br/>";
			for (var j=0; j<i; j++)
				taxString += "&nbsp;&nbsp;";
			taxString += taxonomy[i];
		}
//		addGenomeRow("Taxonomy", taxString);
	}
	$('#gTax').html(taxString);

}

var populateFeatureIds = function(fids) {
	$('#gFeats').html(fids[genome.id].length);
}

/**
 * function: showContig()
 * params:
 *   none
 * returns:
 *   nothing
 * ----------------------
 * Just set up as a wrapper around showContigCircular. Other methods can be plugged in here, maybe later.
 */
var showContig = function() {
	//showContigCircular(); 
	var contig = $("#contigMenu option:selected").val();
	contigWidget.setContig(contig);

	//update the widget
};

/**
 * function: toggleView($toShow)
 * params:
 *   $toShow = the jQuery variable containing the container that should be shown
 * returns:
 *   nothing
 * -----------------------------
 * Hides all containers, then shows the one given by its jQuery variable $toShow.
 * Note that $toShow should probably be a div or other container that can respond
 * to the bootstrap .hide() or .show() in a good way.
 */
var toggleView = function($toShow) {
	$("#contigContainer").hide();
	$("#gcContainer").hide();
	$("#taxContainer").hide();

	$toShow.show();
};

/**
 * function: addGenomeRow
 * params:
 *   name = the string for the name (first) field
 *   value = the string for the value (second) field
 * returns:
 *   nothing
 * -------------------------------------------------
 * Just a little accessory function that adds a new row to the genome info table with a new name and value.
 */
var addGenomeRow = function(name, value) {
	$("#genomeInfoTable").append("<tr><td><strong>" + name + "</strong></td><td>" + value + "</td></tr>");
};

/**
 * function: numberFormatComma(n)
 * params:
 *   n = the number string to format
 * returns:
 *   a formatted number string with commas in the right places.
 * ------------------------------------------------------------
 * Formats a number so that it contains commas in the right (American-style) places.
 * E.g., 12345678.90 is returned as 12,345,678.90.
 */
var numberFormatComma = function(n) {
	var x = n.split('.');
	var intPart = x[0];
	var decPart = x.length > 1 ? '.' + x[1] : '';

	var regex = /(\d+)(\d{3})/;
	while (regex.test(intPart)) {
		intPart = intPart.replace(regex, '$1' + ',' + '$2');
	}
	return intPart + decPart;
};

/**
 * function: extractIdFromLocation
 * params:
 *   none
 * returns:
 *   a KBase id extracted from the URL, or undefined if one isn't present.
 * -----------------------------------------------------------------------
 * Extracts the KBase genome id from the current URL, if one's there.
 * It specifically looks for the string: id=kb|g.XXXXXX
 * so that it only gets KBase genome ids.
 */
var extractIdFromLocation = function() {
	var id = location.href.match(/id\=(kb\|g\.\d+)/);
	if (id.length === 2)
		return(id[1]);
};

/** 
 * function: makeContigDropdown(dropdownId, containerId, func)
 * params:
 *   dropdownId = the id of the dropdown menu
 *   containerId = the id of the dropdown's container
 *   func = the name of the function to be called when a menu item is selected
 * returns:
 *   nothing
 * --------------------------------------------
 * This constructs a dropdown menu with a little bit of contig information in each menu item. When an item is
 * selected it fires off the function given in func.
 * 
 * This assumes that the whole data population process has been completed.
 */
var makeContigDropdown = function(contigTuples, dropdownId, containerId, func) {
	var dropdownHTML =
		"<div>Contig: <select id='" + dropdownId + "' align='center' onchange=\"" + func + "\"></select></div>";
	$(containerId).html(dropdownHTML);

	// populate the dropdown menu
	for (var i=0; i<contigTuples.length; i++) {
		$("#" + dropdownId).append("<option value='" + contigTuples[i][0] + "'>" +
			                  	   contigTuples[i][0] + " - " +
			                  	   contigTuples[i][1] + " bp" +
			                  	   "</option>");
	}

	// add a to workflow button after the menu -- DISABLED FOR NOW
//	$(containerId).append("<div class='span2'>" + toWorkflowButton + "</div>");
};

/**
 * function: getStartAngle(feature)
 * params:
 *   feature = a feature object as above
 * returns:
 *   a decimal start angle in radians
 * -------------------------------------
 * Uses the feature's location info to infer where its block should start on a circle.
 * Used with showContigCircular()
 */
var getStartAngle = function(feature) {
	if (feature.feature_location === undefined || feature.feature_location[0] === undefined) {
		return 0;
	}
	return feature.feature_location[0][1] / contigs[feature.feature_location[0][0]].length * 2 * Math.PI;
};

/**
 * function: getEndAngle(feature)
 * params:
 *   feature = a feature object as above
 * returns:
 *   a decimal end angle in radians
 * -------------------------------------
 * Uses the feature's location info to infer where its block should end on a circle.
 * Used with showContigCircular()
 */
var getEndAngle = function(feature) {
	if (feature.feature_location === undefined || feature.feature_location[0] === undefined) {
		return 0;
	}
	return feature.feature_length / contigs[feature.feature_location[0][0]].length * 2 * Math.PI + getStartAngle(feature);	
};

/**
 * function: getInnerRadius(feature)
 * params:
 *   feature = a feature object as above
 * returns:
 *	 150 px
 * ---------------------------------
 * Calculates the inner radius of a feature on a circle, currently just a constant.
 * Used with showContigCircular()
 */
var getInnerRadius = function(feature) {
	return 150;
};

/**
 * function: getOuterRadius(feature)
 * params:
 *   feature = a feature object as above
 * returns:
 *   200 px
 * -------------------------------------
 * Calculates the outer radius of a feature on a circle, currently just a constant.
 * Used with showContigCircular()
 */
var getOuterRadius = function(feature) {
	return 200;
};

// var displayFeatureData = function(element) {
// 	console.log("id: " + element.feature_id);
// 	console.log("genome name: " + element.genome_name);
// 	console.log("function: " + element.feature_function);
// 	console.log("length: " + element.feature_length);
// 	console.log("pubs: " + element.feature_publications);
// 	console.log("location: " + element.feature_location);
// }

/**
 * function: hoverHighlight(element, d, i)
 * params:
 *   element = an SVG element
 *   d = the feature to be highlighted
 *   i = the index of the feature to be highlighted
 * returns:
 *   nothing
 * ------------------------------------------------
 * Highlights the selected element based on its represented feature and index.
 */
var hoverHighlight = function(element, d, i) {
	d3.select(element)
	  .style("fill",
	  		   d3.rgb(d3.select(element)
	  		     .style("fill"))
	  		     .brighter()
	  		 );
};

/**
 * function: hoverUnhighlight(element, d, i)
 * params:
 *   element = an SVG element
 *   d = the feature to be unhighlighted
 *   i = the index of the feature to be unhighlighted
 * returns:
 *   nothing
 * --------------------------------------------------
 * Removes highlighting from the selected element based on its represented feature and index.
 */
var hoverUnhighlight = function(element, d, i) {
	if (!d3.select(element).classed("highlight"))
		d3.select(element)
		  .style("fill", colorList(i));
};

/**
 * function: selectHighlight(element, d, i)
 * params:
 *   element = an SVG element
 *   d = the feature to be highlighted
 *   i = the index of the feature to be highlighted
 * returns:
 *   nothing
 * ------------------------------------------------
 * Intended to be called when a user clicks on a feature (or otherwise selects it),
 * this gives a bright highlight to the element, and displays basic feature data in
 * specific fields.
 */
var selectHighlight = function(element, d) {
	d3.selectAll(".highlight")
	  .classed("highlight", false)
	  .style("fill", "red");

	d3.select(element)
	  .classed("highlight", true)
	  .style("fill", "yellow");

	var fid = d.feature_id;
	if (fid === undefined)
		fid = "";

	var fFunction = d.feature_function;
	if (fFunction === undefined)
		fFunction = "";

	var fLength = d.feature_length;
	if (fLength === undefined)
		fLength = "";

	var str = '<blockquote>' + 
		   		'<p><b>Function:</b> ' + fFunction + ' &nbsp; &nbsp; <b> Sequence Size:</b> ' + fLength + 'bp' + ' &nbsp; &nbsp; &nbsp; <a href="/services/search/details/' + fid + '"> <i class="icon-check" ></i> ' + fid + '</a></p>'+
			  '</blockquote>';
	$('#featureInfoContainer').html(str);
};

/**
 * function: calcFillColor(feature)
 * params:
 *   feature = a feature, as described elsewhere
 * returns:
 *   the color blue (well, for now)
 * -------------------------------------------
 * Calculates the color that should be used for a feature. Currently, returns a blue constant.
 * Intended for use with showContigLinear(), but easily adaptable.
 */
var calcFillColor = function(feature) {
	return d3.rgb(0, 0, 255);
};

/**
 * function: calcXCoord(feature)
 * params:
 *   feature = a feature, as described elsewhere
 * returns:
 *   the X-coordinate of the feature in pixels
 * ---------------------------------------------
 * Calculates the X-coordinate of the given feature from its location data.
 * Intended for use with showContigLinear(), but easily adaptable.
 */
var calcXCoord = function(feature) {
	if (feature.feature_location === undefined || feature.feature_location[0] === undefined) {
		return 0;
	}
	return feature.feature_location[0][1] / contigs[feature.feature_location[0][0]].length * svgWidth + 5;
};

/**
 * function: calcYCoord(feature)
 * params:
 *   feature = a feature, as described elsewhere
 * returns:
 *   the Y-coordinate of the feature in pixels
 * -------------------------------------------
 * Calculates the Y-coordinate of the given feature from its location data.
 * Intended for use with showContigLinear(), but easily adaptable.
 */
var calcYCoord = function(feature) {
	if (feature.feature_function === undefined || feature.feature_function.length === 0) {
		return 0;
	}
	return /*featureTypes[feature.feature_function] **/ 10 + 3 + Math.random(50)*100;
};

/**
 * function: calcWidth(feature)
 * params:
 *   feature = a feature, as described elsewhere
 * returns:
 *   the width of the feature in pixels
 * -------------------------------------------
 * Calculates the width of the given feature from its location data.
 * Intended for use with showContigLinear(), but easily adaptable.
 */
var calcWidth = function(feature) {
	return feature.feature_length / contigs[feature.feature_location[0][0]].length * svgWidth;
};

/**
 * function: calcGCContent(seq, winSize, offset)
 * params:
 *   seq = the DNA sequence to calculate on.
 *   winSize = the size of the window for each calculation
 *   offset = how far to slide the window for each calculation.
 * returns:
 *   an array of gc% for each window
 * ----------------------------------------------------------
 * This is a really really simple GC content calculator.
 * It works by sliding a window of winSize along the sequence, jumping
 * offset bases each time. Each calculation figures out the percent of G or C
 * bases in the window and stuffs that answer in an ever-expanding array.
 *
 * At the end, the array is returned.
 */
var calcGCContent = function(seq, winSize, offset) {

	seq = seq.toLowerCase();
	var gcContent = [];

	if (offset === 1) {
		var count = 0;
		for (var i=0; i<winSize; i++) {
			if (seq[i] === 'g' || seq[i] === 'c')
				count++;
		}
		gcContent[0] = count / winSize;

		for (var i=1; i<seq.length - winSize + 1; i++) {
			var prev = seq[i-1];
			var next = seq[i+winSize-1];

			if (prev === 'g' || prev === 'c')
				count--;

			if (next === 'g' || next === 'c')
				count++;

			gcContent[i] = count/winSize;
		}
	}

	else {
		for (var i=0; i<seq.length-winSize; i+=offset) {
			var numGC = 0;
			for (var j=0; j<winSize; j++) {
				if (seq[i+j] === 'g' || seq[i+j] === 'c')
					numGC++;
			}
			gcContent.push(numGC/winSize);
		}
	}

	return gcContent;
};

/**
 * function: showGCContent()
 * params:
 *   none
 * returns:
 *   nothing
 * -------------------------
 * Builds a view that shows GC content for the currently selected contig.
 * It's a little bit clunky in that it's kinda lazy with the GC calculation: if the 
 * contig sequence is less than 10^6 bp, it uses a windowsize of 100 and a single 
 * base offset (as it should), but if it's over 10^6 bp, it uses a windowSize of 1000
 * and an offset of 1000 to clump along the sequence, and prevent rendering millions
 * of little steps on the plot.
 *
 * What it SHOULD do (and will in a later version) is put the GC calculation server-side,
 * only load up what range needs to be seen, and interpolate along that if the zoom is
 * out far enough.
 *
 * Also, it should be zoomable.
 */
var showGCContent = function() {
	if (numLoading > 0) 
		return; 

	toggleView($("#gcContainer"));

	d3.select("#gcViewport")
	  .selectAll("g").remove();
	d3.select("#gcViewport")
	  .selectAll("path").remove();

	var contig = $("#gcMenu option:selected").val();

	$("#gcContainer").append(loadingDiv);

	var sequence = cdmiAPI.contigs_to_sequences([contig])[contig];

	var windowSize = 100;
	var offset = 1;
	if (sequence.length > 1000000) {
		windowSize = 1000;
		offset=1000;
	}

	var data = calcGCContent(sequence, windowSize, offset);

	$("#loading-image").remove();

	var curWidth = document.getElementById("gBrowser").offsetWidth;
	var curHeight = 500;

	//console.log("width = " + curWidth);

	var m = [40, 30, 30, 60];
	var w = curWidth - m[1] - m[3];
	var h = curHeight - m[0] - m[2];

	var x = d3.scale
			  .linear()
			  .domain([0, data.length])
			  .range([0, w]);

	var y = d3.scale
		 	  .linear()
			  .domain([0, 1])
			  .range([h, 0]);

	var yAxisScale = d3.scale
					   .linear()
					   .domain([0, 100])
					   .range([h, 0]);

	var line = d3.svg
				 .line()
				 .x(function(d, i) { return x(i); })
				 .y(function(d) { return y(d); });

	var graph = d3.select("#gcViewport")
				  .attr("transform", "translate(" + m[3] + ", " + m[0] + ")");

	var xAxis = d3.svg
				  .axis()
				  .scale(x)
				  .ticks(8)
				  .tickSize(4)
				  .tickSubdivide(false);

	graph.append("svg:g")
		 .attr("class", "x axis")
		 .attr("transform", "translate(0," + (h-5) + ")")
		 .call(xAxis);

	var yAxisLeft = d3.svg
					  .axis()
					  .scale(yAxisScale)
					  .ticks(4)
				  	  .tickSize(4)
					  .orient("left");

	graph.append("svg:g")
		 .attr("class", "y axis")
		 .call(yAxisLeft);

	graph.append("svg:path").attr("d", line(data)).attr("fill", "none").attr("stroke", "blue");

	graph.append("svg:text")
		 .attr("x", -m[3])
		 .attr("y", curHeight/2 - m[0])
		 .text("GC%")
		 .style("font-weight", "bold");

	graph.append("svg:text")
		 .attr("x", curWidth/3)
		 .attr("y", h+25)
		 .text("Contig Base")
		 .style("font-weight", "bold");
};
