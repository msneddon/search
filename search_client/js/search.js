var cdmi_url = "http://kbase.us/services/cdmi_api/";
var login_url = "https://kbase.us/services/authorization/Sessions/Login/";
var workspace_url = "https://kbase.us/services/workspace_service/";
var fba_url = "https://kbase.us/services/fba_model_services/";
var search_api_url = "https://niya.qb3.berkeley.edu/services/search?";

var genome_landing_page = "http://140.221.84.217/genome_info/showGenome.html?id=";
var feature_landing_page = "http://140.221.84.217/feature_info/feature.html?id=";

var cdmi_api = new CDMI_API(cdmi_url);
var cdmi_entity_api = new CDMI_EntityAPI(cdmi_url);
var workspace_service = new workspaceService(workspace_url);
var fba_service = new fbaModelServices(fba_url);

var numPageLinks = 10;

var selectedCategory;
var searchOptions;

var defaultCategorySorts = {"Genomes": "alphabetical", "Genes": "alphabetical", "Publications": "alphabetical"};

var defaultSearchOptions = {"category": {"Genomes": {"itemsPerPage": 25, "page": 1},
                                         "Genes": {"itemsPerPage": 25, "page": 1},
                                         "Publications" : {"itemsPerPage": 25, "page": 1},
                                         "default": {"itemsPerPage": 25, "page": 1}                                         
                                        }
                            };

var searchCategories = ["Genomes", "Genes", "Publications"];

/*
var searchCategories = {"Central Store": ["CSGenomes", "CSGenes", "CSPublications"],
                        "User Stores": ["WSGenomes", "WSGenes", "WSModels", "WSMedia", "WSFBA", "WSPhenotypeSet"]};
*/
var categoryCounts = {"Genomes": 0, "Genes": 0, "Publications": 0};
var numCounts = 0;


$(window).load(function(){
    $("#login-area").kbaseLogin({style: 'button'});

    searchOptions = defaultSearchOptions;

    $("#searchTextInput").on("keypress", function (evt) {
        if (evt.keyCode === 13) {
            var input = $.trim($('#searchTextInput')[0].value);
            
            if (input !== null && input !== '') {
                startSearch(input,searchOptions);
            }
        }
    });
    
    
    //register for login event, then capture token
    //$(document).on('loggedIn.kbase', function() { var token = $("#login-area").kbaseLogin("session", "token"); });
    //$(document).on('loggedOut.kbase', function() {});
});


function startSearch(queryString, options) {
    if (queryString === null || queryString === '') {
        return;
    }

    searchOptions = {"category": {"Genomes": {"itemsPerPage": 25, "page": 1},
                                  "Genes": {"itemsPerPage": 25, "page": 1},
                                  "Publications" : {"itemsPerPage": 25, "page": 1},
                                  "default": {"itemsPerPage": 25, "page": 1}                                         
                                 }
                    };

    selectedCategory = null;
    
    searchOptions['q'] = queryString;

    $("#categories").empty();
    $("#page-links").empty();
    $("#result-set-list").empty();

    getResults("default", searchOptions);
}



function addAllGenomes() {
    var genomes = {};

    $('.typedRecord').each(function () {
        if ($(this).find('input').prop('checked') === true) {
            var value = $(this).find('#gid')[0].innerText;
            
            if (!genomes.hasOwnProperty(value)) {
                genomes[value] = value;
            } 
        } 
    });
    
    for (var prop in genomes) {
        if (genomes.hasOwnProperty(value)) {
            pushGenomeToWorkspace({"genome": genomes[prop], "workspace": selectedWorkspace, "auth": auth_token});
        }
    }
}


function pushGenomeToWorkspace(genome_id, workspace_id, token) {
    function success(result) {
        console.log("genome import success");
        console.log(result);
    }
    
    function error(result) {
        console.log("genome import failed");
        console.log(result);
    }

    fba_service.genome_to_workspace({"genome": genome_id, "workspace": workspace_id, "auth": token}, success(result), error(result));
}


function setResultsPerPage(category, value) {
    //calculate new starting page
    var itemsPerPage = parseInt(value);
    var page = parseInt(searchOptions["category"][category]['page']);
    var startItem = (page - 1) * searchOptions["category"][category]['itemsPerPage'];
    
    searchOptions["category"][category]['itemsPerPage'] = value;    
    searchOptions["category"][category]['page'] = Math.floor(startItem/itemsPerPage) + 1;
    
    getResults(category, searchOptions);
}


function setSortType(category, value) {
    searchOptions["category"][category]['sortType'] = value;
    getResults(category, searchOptions);
}


function selectCategory(value) {
    console.log(value);
    selectedCategory = value;
    console.log(selectedCategory);
    console.log("category set");
    $("#result-set-header").removeClass('hidden');
    getResults(value, searchOptions);
}


// move to a different page of results
function transitionToPageSet(category, page) {
    searchOptions["category"][category]['page'] = page;
    getResults(category, searchOptions);
}


function selectAll() {
    if ($("#select-all").prop('checked') === true) {
        $("#result-set-list input").prop('checked', true);
    }
    else {
        $("#result-set-list input").prop('checked', false);    
    }
}



function displayCategories() {
    $("#result-set-header").addClass('hidden');
    $("#result-set-list").empty();

    var content = "<tr>";    
    for (var prop in categoryCounts) {
        if (categoryCounts.hasOwnProperty(prop)) {
            content += "<td><a onclick='selectCategory(\"" + prop + "\")'>" + prop + " (" + categoryCounts[prop] + ")</span></td>";    
        }
    }
    content += "</tr>";
    
    $("#result-set-list").append(content);
    $("#all-results").removeClass("hidden");
}



// all the markup for displaying a set of results for a single page
function displayResults(category, jsonResults) {
    console.log(category);
    console.log(jsonResults);

    var currentPage = jsonResults['page'];
    var totalRecords = jsonResults['found'];
    var currentRecords = jsonResults['items'];
    var recordCount = jsonResults['itemCount'];    
    var currentRecordLocation = (currentPage - 1) * searchOptions["category"][category]['itemsPerPage'];
    var totalPages = Math.floor(totalRecords/searchOptions["category"][category]['itemsPerPage']) + 1;
    var currentPageMarker = currentPage % numPageLinks;
    var linksInserted = 0;
    
    if (recordCount > 0) {        
        $("#result-position").html("Displaying results <strong>" + 
                                   (currentRecordLocation + 1) + "-" + (currentRecordLocation + recordCount) + 
                                   "</strong> out of <strong>" + totalRecords + "</strong>.");
        
        $("#result-per-page").val(searchOptions["category"][category]['itemsPerPage']);
        $("#result-sort-type").val(searchOptions["category"][category]['sortType']);
        
        $("#result-set-list").empty();

        var resultItem = "";

        if (selectedCategory === "Genomes") {
            $("#result-set-list").append("<tr><td><label class='checkbox'><input type='checkbox' id='select-all' onchange='selectAll()'></input></label></td>" +
                                         "<td><span style='min-width:80px'><strong>Select all</strong></span></td>" + 
                                         "<td><strong>Type</strong></td>" + "<td><strong>Genome Species</strong></td>" + "<td><strong>Genome Identifier</strong></td>" +
                                         "<td><strong>Genome Sequence Length</strong></td>" + "<td><strong>Contigs</strong></td>" + "<td><strong>Coding Sequences</strong></td>" +
                                         "<td><strong>RNAs</strong></td>" + 
                                         "</tr>");        
                                         
            for (var i = 0; i < recordCount; i++) {
                resultItem = "<tr class='typedRecord'><td><label class='checkbox' id='" + currentRecords[i]['gid'] + "'><input type='checkbox'></input></label></td>" + 
                             "<td><span class='space-right'>" + (currentRecordLocation + i + 1) + ".</span></td>" +
                             "<td><span class='label label-success space-right'><a style='color:white' target='_blank' href='" + genome_landing_page + currentRecords[i]['gid'] + "'>Genome</a></span></td>" + 
                             "<td><span><a class='space-right' target='_blank' href='" + genome_landing_page + currentRecords[i]['gid'] + "'>" +
                             "<strong><em>" + currentRecords[i]['scientific_name'] + "</em></strong>" +
                             "</a></span></td>" +  
                             "<td><span id='gid' class='space-right'>" + currentRecords[i]['gid'] + "</span></td>" +  
                             "<td><span class='space-right'>" + currentRecords[i]['dna_size'] + " bp </span></td>" + 
                             "<td><span>" + currentRecords[i]['contigs'] + "</span></td>" +
                             "<td><span>" + currentRecords[i]['pegs'] + "</span></td>" +
                             "<td><span>" + currentRecords[i]['rnas'] + "</span></td>" +
                             "</tr>";
                $("#result-set-list").append(resultItem);                                                    
            }        
        }
        else if (selectedCategory === "Genes") {
            $("#result-set-list").append("<tr>" +
                                         "<td><label class='checkbox'><input type='checkbox' id='select-all' onchange='selectAll()'></input></label></td>" +
                                         "<td><span style='min-width:80px'><strong>Select all</strong></span></td>" + 
                                         "<td><div><strong>Type<strong></div></td>" +
                                         "<td><div><strong>Genome Species<strong></div></td>" +
                                         "<td><div><strong>Gene Function<strong></div></td>" +
                                         "<td><div><strong>Gene Identifier<strong></div></td>" +
                                         "<td><div><strong>Gene Length<strong></div></td>" +
                                         "</tr>");        

            for (var i = 0; i < recordCount; i++) {
                resultItem = "<tr class='typedRecord'><td><label class='checkbox' id='" + currentRecords[i]['gid'] + "'><input type='checkbox'></input></label></td>" + 
                             "<td><span class='space-right'>" + (currentRecordLocation + i + 1) + ".</span></td>" +
                             "<td><span class='label label-success space-right'><a style='color:white' target='_blank' href='" + feature_landing_page + currentRecords[i]['fid'] + "'>Feature</a></span></td>" + 
                             "<td><span><a class='nowrap space-right' target='_blank' href='" + genome_landing_page + currentRecords[i]['gid'] + "'>" +
                             "<strong><em>" + currentRecords[i]['scientific_name'] + "</em></strong>" +
                             "</a></span></td>" +  
                             "<td><span><a class='space-right' target='_blank' href='" + feature_landing_page + currentRecords[i]['fid'] + "'>" +
                             "<strong>" + currentRecords[i]['function'] + "</strong>" +
                             "</a></span></td>" +                           
                             "<td><span class='space-right'>" + currentRecords[i]['fid'] + "</span></td>" +                           
                             "<td><span class='nowrap'>" + currentRecords[i]['sequence_length'] + " bp </span></td>" +
                             "</tr>";                    
                $("#result-set-list").append(resultItem);                                 
            }                
        }
        else if (selectedCategory === "Publications") {
            $("#result-set-list").append("<tr>" + 
                                         "<td><span></span></td>" +
                                         "<td><span><strong>Type</strong></span></td>" + 
                                         "<td><span><strong>Pubmed Identifier</strong></span></td>" + 
                                         "<td><span><strong>Title</strong></span></td>" + 
                                         "</tr>");        

            for (var i = 0; i < recordCount; i++) {
                resultItem = "<tr><td><span class='space-right'>" + (currentRecordLocation + i + 1) + ".</span></td>" +
                             "<td><span class='label label-success space-right'><a style='color:white' target='_blank' href='" + currentRecords[i]['link'] + "'>Publication</a></span></td>" + 
                             "<td><span class='nowrap space-right'>" + currentRecords[i]['pid'] + "</span></td>" +                           
                             "<td><span><a target='_blank' href='" + currentRecords[i]['link'] + "'>" +
                             "<strong>" + currentRecords[i]['title'] + "</strong>" +
                             "</a></span></td>" +  
                             "</tr>";                                                                 
                $("#result-set-list").append(resultItem);
            }        
        }
        else {
            console.log("Unknown Type");
            console.log(selectedCategory);        
        }        
            
        
        
        // set the pagination controls
        $("#page-links").empty();
        
        // if we are on page numPageLinks, we need to make sure the position is not 0
        if (currentPageMarker === 0) {
            currentPageMarker = numPageLinks;
        }
         
        // check to see if we should present a link to the last page of the previous page set       
        if (currentPage > 1 && currentPage > numPageLinks) {
            $("#page-links").append("<li><a onclick='transitionToPageSet(\"" + (selectedCategory) + "\"," + (currentPage - currentPageMarker) + ")'><</a></li>");            
        }
        
        // insert links for all the pages up to the current page in this page set
        for (var p = currentPage - currentPageMarker + 1; p < currentPage; p++, linksInserted++) {
            $("#page-links").append("<li><a onclick='transitionToPageSet(\"" + (selectedCategory) + "\"," + p + ")'>" +  p + "</a></li>");            
        }                 

        // insert the link for the current page and highlight it as the active page              
        $("#page-links").append("<li class='active'><a onclick='transitionToPageSet(\"" + (selectedCategory) + "\"," + currentPage + ")'>" + currentPage + "</a></li>");            
        linksInserted++;

        // make sure that we have results for all the remaining page links  
        if (totalPages > currentPage + (numPageLinks - linksInserted)) { 
            // insert the links for the default size page set
            for (var p = currentPage + 1; p < currentPage + (numPageLinks - linksInserted) + 1; p++) {
                $("#page-links").append("<li><a onclick='transitionToPageSet(\"" + (selectedCategory) + "\"," + p + ")'>" +  p + "</a></li>");            
            }                 
            // insert the link to the next set of pages
            $("#page-links").append("<li><a onclick='transitionToPageSet(\"" + (selectedCategory) + "\"," + (currentPage + (numPageLinks - linksInserted) + 1) + ")'>></a></li>");            
        }
        else {
            // insert the links for the actual remaining page set                
            for (var p = currentPage + 1; p < totalPages + 1; p++) {
                $("#page-links").append("<li><a onclick='transitionToPageSet(\"" + (selectedCategory) + "\"," + p + ")'>" + p + "</a></li>");            
            }
        }                                  
    }
    else {
        $("#result-position").html("No results found.");        
    }
    
    
    // display categories
    $("#categories").empty();
    
    var keys;
    for (var i = 0; i < searchCategories.length; i++) {
        $("#categories").append("<div class='row-fluid'><a class='category-link btn btn-link' onclick='selectCategory(\"" + 
                                searchCategories[i] + "\")'>" + searchCategories[i] + "   (" + categoryCounts[searchCategories[i]] + ")</a></div>");
    }    
    
    $("#all-results").removeClass("hidden");    
}



function displayCount(category) {
    $("#count-" + category).empty().append(categoryCounts[category]);    
}



function getCount(options, category) {
    var queryOptions = {};
    
    for (var prop in options) {
        queryOptions[prop] = options[prop];        
    }
    
    queryOptions["itemsPerPage"] = 0;
    queryOptions["category"] = category;

    jQuery.ajax({
        type: 'GET',
        contentType: 'application/json',
        url: search_api_url + "callback=?",
        data: queryOptions,      
        dataType: 'jsonp',
        success: function success (jsonResult) {
            if (typeof jsonResult !== 'undefined') {
                categoryCounts[category] = jsonResult['found'];
            }
            else {
                categoryCounts[category] = 0;
            }
            
            numCounts += 1;
            
            displayCount(category);
            if (numCounts === searchCategories.length) {
                displayCategories();
            }
        },
        error: function (errorObject) {
            categoryCounts[category] = 0;
            numCounts += 1;
            
            displayCount(category);
            if (numCounts === searchCategories.length) {
                displayCategories();
            }            
        }
    });
}


function getResults(category, options) {
    if (selectedCategory === null) {
        var queryOptions = {'q': options['q']};

        numCounts = 0;
        for (var i = 0; i < searchCategories.length; i++) {
            getCount(queryOptions, searchCategories[i]);            
        }
        
        return;
    }

    var queryOptions = {};
    
    queryOptions["category"] = selectedCategory;
    for (var prop in options) {        
        if (prop !== "category") {
            queryOptions[prop] = options[prop];
        }
        else {
            for (var cat_prop in options["category"][selectedCategory]) {
                queryOptions[cat_prop] = options["category"][selectedCategory][cat_prop];
            }
        }    
    }
    
    jQuery.ajax({
        type: 'GET',
        contentType: 'application/json',    
        url: search_api_url + "callback=?",
        data: queryOptions,      
        dataType: 'jsonp',
        success: function success(jsonResult) {
            return typeof jsonResult === 'undefined' ? false : displayResults(category, jsonResult);
        },
        error: function(errorObject) {
            console.log(errorObject);
        }
    });        

}


function showLoadingMessage(message, element) {
    if (element === undefined || element === null) {
        if (message && message.length > 0) {
            $("#loading_message_text").empty();
            $("#loading_message_text").append(message);
        }
        
        $.blockUI({message: $("#loading_message")});    
    }
    else {
        $(element).block({message: "<div><div>" + message + "</div><div><img src='assets/img/loading.gif'/></div></div>"});    
    }
}


function hideLoadingMessage(element) {
    if (element === undefined || element === null) {
        $.unblockUI();
        $("#loading_message_text").empty();
        $("#loading_message_text").append("Loading, please wait...");
    }
    else {
        $(element).unblock();
    }        
}

function login(user_id, password) {
    var initializeUser = function (token) {
        userData = jQuery.extend(true, {}, defaultUserData);
        userData.auth_token = token;
           
        $("#login_status").text("User : " + user_id);
        $("#login_status").effect('slide');

        $("#logout").prop('width',$('#login_status').outerWidth());
       
        $("#new_login").addClass("hidden");
        $("#main_app").removeClass("hidden");
        displaySelectWorkspace();
    };


    var hasLocalStorage = false;

    if (localStorage && localStorage !== null) {
        hasLocalStorage = true;
    }

    var options = {
        loginURL : login_url,
        possibleFields : ['verified','name','opt_in','kbase_sessionid','token','groups','user_id','email','system_admin'],
        fields : ['token', 'kbase_sessionid', 'user_id']
    };

    var args = { "user_id" : user_id, "password": password, "fields": options.fields.join(',')};
    
    login_result = $.ajax({type: "POST",
                          url: options.loginURL,
                          data: args,
                          beforeSend: function (xhr) {
                                          showLoadingMessage("Logging you into KBase as " + user_id);
                                      },
                          success: function(data, textStatus, jqXHR) {
                                       if (hasLocalStorage) {
                                           localStorage["auth_token"] = data.token;
                                       }
                                       
                                       initializeUser(data.token);
                                   }, 
                          error: function(jqXHR, textStatus, errorThrown) {
                              console.log(errorThrown);
                              $("#login_error").append(errorThrown.message);                              
                          },
                          dataType: "json"});
}

function logout() {
    //resetApplication(userData);

    var hasLocalStorage = false;

    if (localStorage && localStorage !== null) {
        hasLocalStorage = true;
    }

    if (hasLocalStorage) {
        localStorage.clear();
    }
    
    userData = null;
    $("#main_app").addClass("hidden");
    $("#new_login").removeClass("hidden");   
    
    location.reload(); 
}

