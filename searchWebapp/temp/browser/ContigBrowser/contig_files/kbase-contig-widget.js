/*
 * KBase Genome Browser Widget
 * ---------------------------
 * This is designed as a widget to be inserted where ever it's needed.
 * I'm not sure how to get the sizing right, so we'll start with something static,
 * then move on later to configurable sizes.
 *
 * Bill Riehl
 * wjriehl@lbl.gov
 * Lawrence Berkeley National Lab
 * October 23, 2012
 */

// global API definitions
var apiURL = "http://www.kbase.us/services/cdmi_api/";
var proteinInfoURL = "http://140.221.84.194:7057/";
var cdmiAPI = new CDMI_API(apiURL);
var entityAPI = new CDMI_EntityAPI(apiURL);
var proteinInfoAPI = new ProteinInfo(proteinInfoURL);

var widget;

var onClickUrl;
var onClickFunction;
// SVG, etc. parameters (made global for convenient wiggling)
var svgWidth = 1165;
var svgHeight = 500;

var trackMargin = 5;
var trackThickness = 15;
var leftMargin = 5;
var topMargin = 20;
var arrowSize = 10;
var allowResize = false;
var numTracks = 0;

var centerFeature;

var start = 1;
var length = 10000;

// tooltip inspired from
// https://gist.github.com/1016860
var tooltip = d3.select("body")
				.append("div")
				.style("position", "absolute")
				.style("z-index", "10")
				.style("visibility", "hidden")
				.style("opacity", "0.8")
				.style("background-color", "#222222")
				.style("color", "#FFF")
				.style("padding", "0.5em")
				.text("");

// Make a track object.
var track = function() {
	var that = {};

	that.regions = [];
	that.min = Infinity;
	that.max = -Infinity;
	that.numRegions = 0;

	that.addRegion = function(feature_location) {
		for (var i=0; i<feature_location.length; i++) {

			var start = Number(feature_location[i][1]);
			var length = Number(feature_location[i][3]);
			var end = start + length;

			if (start > end) {
				var x = end;
				end = start;
				start = x;
			}

			this.regions.push([start, end]);
			if (start < this.min)
				this.min = start;
			if (end > this.max)
				this.max = end;
			this.numRegions++;
		}
	};

	that.hasOverlap = function(feature_location) {
		for (var i=0; i<feature_location.length; i++) {
			var start = Number(feature_location[i][1]);
			var length = Number(feature_location[i][3]);
			var end = (feature_location[i][2] === "+" ? start + length - 1 :
														start - length + 1);

			// double check the orientation
			if (start > end) {
				var x = end;
				end = start;
				start = x;
			}

			/* cases:
			 * simple ones:
			 *  [start, end] [min]
			 *  [max] [start, end]
			 * less simple:
			 *  look over all regions
			 */
			for (var ii=0; ii<this.regions.length; ii++) {
				var region = this.regions[ii];
				// region = [start,end] pair
				if ((start >= region[0] && start <= region[1]) ||
					(end >= region[0] && end <= region[1]) ||
					(start <= region[0] && end >= region[1])) {
					return true;
				}
			}
			
		}
		return false;
	};

	return that;
};


/**
 * function: genomeWidget(contig, start, length, target)
 * params:
 *   contig = KBase id of the desired contig
 *   start = starting base of the contig for rendering (i.e. left side of the widget)
 *   length = length of the contig region of interest in bp
 *   target = the DOM target id for the widget
 */
var contigWidget = function(contig, start, length, target) {

	var that = {
		contig : contig,
		start : start,
		length : length,
		target : target,
	};

	that.updateContig = function(contigId) {
		that.contig = contigId;
		cdmiAPI.contigs_to_lengths([that.contig], function(contigLength) {
			that.contigLength = parseInt(contigLength[that.contig]);
			that.start = 0;
			if (that.length > that.contigLength)
				that.length = that.contigLength;
		});
	};

	// not sure where else to put it, so this goes here.
	// probably not ideal, but that's how it goes.
	that.updateContig(that.contig);

	that.setGenome = function(genomeId) {
		that.genomeId = genomeId;
		var genomeList = cdmiAPI.genomes_to_contigs([genomeId], function(genomeList) {
			// populate the contig dropdown with the list of contigs, and start with the first one.
			setContig(genomeList[genomeId][0]);
		});

	};

	that.setContig = function(contigId) {
		// set contig info and re-render
		that.updateContig(contigId);
		that.updateWidget();
	};

	that.setRange = function(start, length) {
		// set range and re-render
		that.start = start;
		that.length = length;
		that.updateWidget();
	};

	/*
	 * Figures out which track each feature should be on, based on starting point and length.
	 */
	var processFeatures = function(features) {

		var tracks = [];
		tracks[0] = track(); //init with one track.

		// First, transform features into an array instead of an object.
		// eg., take it from {'fid' : <feature object>, 'fid' : <feature object> }
		// to [<feature object>, <feature object> ... ]

		var feature_arr = [];
		for (fid in features) {
			feature_arr.push(features[fid]);
		}

		features = feature_arr;

		// First, sort the features by their start location (first pass = features[fid].feature_location[0][1], later include strand)
		features.sort(function(a, b) {
			return a.feature_location[0][1] - b.feature_location[0][1];
		});

		operonGenes = proteinInfoAPI.fids_to_operons([centerFeature], 
			//on success
			function(operonGenes) {
				operonGenes = operonGenes[centerFeature];

			}
		);

		// Foreach feature...
		for (var j=0; j<features.length; j++) {
			var feature = features[j];

			// Look for an open spot in each track, fill it in the first one we get to, and label that feature with the track.
			var start = Number(feature.feature_location[0][1]);
			var length = Number(feature.feature_location[0][3]);
			var end;

			if (feature.feature_location[0][2] === "+") {
				end = start + length - 1;
			}
			else {
				start = start - length + 1;
				end = start + length;
			}

			for (var i=0; i<tracks.length; i++) {
				if (!(tracks[i].hasOverlap(feature.feature_location))) {
					tracks[i].addRegion(feature.feature_location);
					feature.track = i;
					break;
				}
			}
			// if our feature doesn't have a track yet, then they're all full in that region.
			// So make a new track and this feature to it!
			if (feature.track === undefined) {
				var next = tracks.length;
				tracks[next] = track();
				tracks[next].addRegion(feature.feature_location);
				feature.track = next;
			}
		}

		numTracks = tracks.length;
		return features;
	}

	that.updateWidget = function(useCenter) {
		// updates the widget based on loaded info.
		// fetches all feature info in the range and renders the d3 object.
		if (centerFeature && useCenter)
			cdmiAPI.fids_to_feature_data([centerFeature], that.renderFromCenter);
		else
			cdmiAPI.region_to_fids([that.contig, that.start, '+', that.length], that.getFeatureData);
	}

	that.renderFromCenter = function(feature) {
		if (feature) {
			feature = feature[centerFeature];

			// set it up so that we have the same length of contig region, but our foi range is in the middle.
			// basically, we just need to reset that.start to be correct.
			that.start = Math.max(0, Math.floor(parseInt(feature.feature_location[0][1]) + (parseInt(feature.feature_location[0][3])/2) - (that.length/2)));
			
		}
		else {
			window.alert("Error: fid '" + centerFeature + "' not found! Continuing with original range...");
		}
		cdmiAPI.region_to_fids([that.contig, that.start, '+', that.length], that.getFeatureData);
	}

	that.getFeatureData = function(fids) {
		cdmiAPI.fids_to_feature_data(fids, that.getOperonData);
	}

	that.getOperonData = function(features) {
		proteinInfoAPI.fids_to_operons([centerFeature],
			function(operonGenes) {
				operonGenes = operonGenes[centerFeature];

				for (var j in features) {
					for (var i in operonGenes)
					{
						if (features[j].feature_id === operonGenes[i])
							features[j].isInOperon = 1;
					}
				}

				that.renderFromRange(features);

			});
	}


	function adjustHeight() {
		var neededHeight = numTracks * (trackThickness + trackMargin) + topMargin + trackMargin;

		if (neededHeight > d3.select("#contigWidget").attr("height")) {
			d3.select("#contigWidget")
			  .attr("height", neededHeight);
		}
	}

	that.renderFromRange = function(features) {
		features = processFeatures(features);

		if (allowResize)
			adjustHeight();

		var trackSet = that.trackContainer.selectAll("path")
						                  .data(features, function(d) { return d.feature_id; });

		trackSet.enter()
  			 	.append("path")
      			 	 .attr("class", "feature")  // incl feature_type later (needs call to get_entity_Feature?)
		  			 .attr("id", function(d) { return d.feature_id; })
					 .attr("stroke", "black")
					 .attr("fill", function(d) { return calcFillColor(d); })
					 .on("mouseover", function(d) { d3.select(this).style("fill", d3.rgb(d3.select(this).style("fill")).darker()); 
					 							   tooltip = tooltip.text(d.feature_id + ": " + d.feature_function);
					 							   return tooltip.style("visibility", "visible"); })
					 .on("mouseout", function() { d3.select(this).style("fill", d3.rgb(d3.select(this).style("fill")).brighter()); return tooltip.style("visibility", "hidden"); })
					 .on("mousemove", function() { return tooltip.style("top", (d3.event.pageY+15) + "px").style("left", (d3.event.pageX-10)+"px"); })
					 .on("click", function(d) { if (onClickFunction) {
					 								onClickFunction(this, d);
					 							}
					 							else {
					 								highlight(this, d); 
					 							}
					 						});

		trackSet.exit()
				.remove();

		trackSet.attr("d", function(d) { return featurePath(d); });



		
		that.xScale = that.xScale
				  		  .domain([that.start, that.start + that.length]);
		
		

		that.xAxis = that.xAxis
					     .scale(that.xScale);
        
		that.axisSvg.call(that.xAxis);
        

	};

	function featurePath(feature) {
		var path = "";

		var coords = [];

		// draw an arrow for each location.
		for (var i=0; i<feature.feature_location.length; i++) {
			var location = feature.feature_location[i];

			var left = calcXCoord(location);
			var top = calcYCoord(location, feature.track);
			var height = calcHeight(location);
			var width = calcWidth(location);

			coords.push([left, left+width]);

			if (location[2] === '+')
				path += featurePathRight(left, top, height, width) + " ";
			else
				path += featurePathLeft(left, top, height, width) + " ";
		}

		// if there's more than one path, connect the arrows with line segments
		if (feature.feature_location.length > 1) {
			// sort them
			coords.sort(function(a, b) {
				return a[0] - b[0];
			});

			var mid = calcYCoord(feature.feature_location[0], feature.track) + calcHeight(feature.feature_location[0])/2;

			for (var i=0; i<coords.length-1; i++) {
				path += "M" + coords[i][1] + " " + mid + " L" + coords[i+1][0] + " " + mid + " Z ";
			}
			// connect the dots
		}
		return path;
	};

	function featurePathRight(left, top, height, width) {
		// top left
		var path = "M" + left + " " + top;

		if (width > arrowSize) {
			// line to arrow top-back
			path += " L" + (left+(width-arrowSize)) + " " + top +
			// line to arrow tip
					" L" + (left+width) + " " + (top+height/2) +
			// line to arrow bottom-back
					" L" + (left+(width-arrowSize)) + " " + (top+height) +
			// line to bottom-left edge
					" L" + left + " " + (top+height) + " Z";
		}
		else {
			// line to arrow tip
			path += " L" + (left+width) + " " + (top+height/2) +
			// line to arrow bottom
					" L" + left + " " + (top+height) + " Z";
		}
		return path;
	};

	function featurePathLeft(left, top, height, width) {
		// top right
		var path = "M" + (left+width) + " " + top;

		if (width > arrowSize) {
			// line to arrow top-back
			path += " L" + (left+arrowSize) + " " + top +
			// line to arrow tip
					" L" + left + " " + (top+height/2) +
			// line to arrow bottom-back
					" L" + (left+arrowSize) + " " + (top+height) +
			// line to bottom-right edge
					" L" + (left+width) + " " + (top+height) + " Z";
		}
		else {
			// line to arrow tip
			path += " L" + left + " " + (top+height/2) +
			// line to arrow bottom
					" L" + (left+width) + " " + (top+height) + " Z";
		}
		return path;
	};

	function calcXCoord(location) {
		var x = location[1];
		if (location[2] === "-")
			x = location[1] - location[3];

		return (x-that.start) / that.length * svgWidth + leftMargin;	
	};

	function calcYCoord(location, track) {
		return topMargin+trackMargin + trackMargin*track + trackThickness*track;
	};

	function calcWidth(location) {
		return location[3] / that.length * svgWidth;
	};

	function calcHeight(location) {
		return trackThickness;
	}

	function calcFillColor(feature) {
		if (feature.feature_id === centerFeature)
			return "#00F";
		if (feature.isInOperon === 1)
			return "#0F0";
		return "#F00";
		// should return color based on feature type e.g. CDS vs. PEG vs. RNA vs. ...
	};

	function highlight(element, feature) {
		// unhighlight others - only highlight one at a time.
		// if ours is highlighted, recenter on it.

		
		recenter(feature);
		return; // skip the rest for now.

		if (d3.select(element).attr("id") === feature.feature_id &&
			d3.select(element).classed("highlight")) {
			recenter(feature);
		}
		else {
			d3.select(".highlight")
			  .classed("highlight", false)
			  .style("fill", function(d) { return calcFillColor(d); } );

			d3.select(element)
			  .classed("highlight", true)
			  .style("fill", "yellow");
		}
	}

	function recenter(feature) {
		centerFeature = feature.feature_id;
		if (onClickUrl)
			onClickUrl(feature.feature_id);
		else
			that.updateWidget(true);
	};

	that.init = function() {
		// initialize the widget DOM & SVG elements. Buttons and such.
		// then make the widget.
		if (that.target.charAt[0] !== '#')
			that.target = "#" + that.target;

		// Init the SVG container to be the right size.
		that.svg = d3.select(that.target)
					 .append("svg")
					 .attr("width", svgWidth)
					 .attr("height", svgHeight)
					 .attr("id", "contigWidget");

		that.trackContainer = that.svg.append("g");

		that.xScale = d3.scale.linear()
				  		.domain([that.start, that.start + that.length])
				  		.range([0, svgWidth]);

		that.xAxis = d3.svg.axis()
					   .scale(that.xScale)
					   .orient("top")
					   .tickFormat(d3.format(",.0f"));

		that.axisSvg = that.svg.append("g")
						.attr("class", "axis")
						.attr("transform", "translate(0, " + topMargin + ")")
						.call(that.xAxis);

		that.updateWidget(true);
	};

	that.moveLeftEnd = function() {
		that.start = 0;
		that.updateWidget();
	}

	that.moveLeftStep = function() {
		that.start = Math.max(0, that.start - Math.ceil(that.length/2));
		that.updateWidget();
	}

	that.zoomIn = function() {
		that.start = Math.min(that.contigLength-Math.ceil(that.length/2), that.start + Math.ceil(that.length/4));
		that.length = Math.max(1, Math.ceil(that.length/2));
		that.updateWidget();
	}

	that.zoomOut = function() {
		that.length = Math.min(that.contigLength, that.length*2);
		that.start = Math.max(0, that.start - Math.ceil(that.length/4));
		if (that.start + that.length > that.contigLength)
			that.start = that.contigLength - that.length;
		that.updateWidget();
	}

	that.moveRightStep = function() {
		that.start = Math.min(that.start + Math.ceil(that.length/2), that.contigLength - that.length);
		that.updateWidget();
	}

	that.moveRightEnd = function() {
		that.start = that.contigLength - that.length;
		that.updateWidget();
	}

	return that;
};

var makeContigWidget = function(target, w, h, options) {
	/* Logic:
	 * If there's a feature and no contig, get the feature data and send everything to
	 * makeContigWidgetFromFeature
	 *
	 * If there'a a contig and not feature, send it to
	 * makeContigWidgetFromContig
	 * 
	 * If 
	 */

	svgHeight = h;
	svgWidth = w;

	if (options) {
		if (options.hasOwnProperty("arrowSize")) {
			if (isNumber(options.arrowSize))
				arrowSize = options.arrowSize;
		}
		if (options.hasOwnProperty("trackThickness")) {
			if (isNumber(options.trackThickness))
				trackThickness = options.trackThickness;
		}
		if (options.hasOwnProperty("start")) {
			start = options.start;
		}
		if (options.hasOwnProperty("length")) {
			length = options.length;
		}
		if (options.hasOwnProperty("onClickUrl")) {
			onClickUrl = function(id) {
				window.open(options.onClickUrl + id, "_self");
			}
		}
		if (options.hasOwnProperty("onClickFunction")) {
			onClickFunction = options.onClickFunction;
		}
		if (options.hasOwnProperty("allowResize")) {
			allowResize = options.allowResize;
		}
	}

	if (!target) {
		target = "body";
	}

	if (options && options.hasOwnProperty("feature")) {
		// keep the same length, but center the widget around the given feature.
		// throw an error if it isn't found.
		centerFeature = options.feature;
		// figure out contig from the feature id
		var featureData = cdmiAPI.fids_to_feature_data([centerFeature], 
		
			function(featureData) {
				contig = featureData[centerFeature].feature_location[0][0];
				widget = contigWidget(contig, start, length, target);
				widget.init();
				return widget;
			},

			function(error) {
				window.alert("Error: unknown Feature ID: '" + centerFeature + "'");
			}

		);
	}
	else if (options && options.hasOwnProperty("contig")) {
		// use the contig to set things up.
		if (options.hasOwnProperty("contig")) {
			contig = options.contig;
			widget = contigWidget(contig, start, length, target);
			widget.init(); 
			return widget;
		}

	}
	else {
		window.alert("Error: contig information not found!\nUnable to construct contig viewer!");
		return;
	}
};

//curl -X POST http://www.kbase.us/services/cdmi_api -d '{"params":[[[["kb|g.20848.c.0",1,"-",100]]]],"method":"CDMI_API.locations_to_dna_sequences","version":"1.1"}'
//curl -X POST http://www.kbase.us/services/cdmi_api -d '{"params":[["kb|g.20848.c.0",1,"+",10000]],"method":"CDMI_API.region_to_fids","version":"1.1"}'
