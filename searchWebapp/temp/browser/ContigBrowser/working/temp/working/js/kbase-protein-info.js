

function ProteinInfo(url, auth, auth_cb) {

    var _url = url;

    var _auth = auth ? auth : { 'token' : '', 'user_id' : ''};
    var _auth_cb = auth_cb;


    this.fids_to_operons = function (fids, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.fids_to_operons",
            [fids], 1, _callback, _errorCallback);
    };

    this.fids_to_domains = function (fids, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.fids_to_domains",
            [fids], 1, _callback, _errorCallback);
    };

    this.domains_to_domain_annotations = function(domain_ids, _callback, _error_callback)
    {
        return json_call_ajax("ProteinInfo.domains_to_domain_annotations", 
            [domain_ids], 1, _callback, _error_callback);
    };

    this.fids_to_domain_hits = function(fids, _callback, _error_callback)
    {
        json_call_ajax("ProteinInfo.fids_to_domain_hits", 
            [fids], 1, _callback, _error_callback);
    };

    this.domains_to_fids = function (domain_ids, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.domains_to_fids",
            [domain_ids], 1, _callback, _errorCallback);
    };

    this.fids_to_ipr = function (fids, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.fids_to_ipr",
            [fids], 1, _callback, _errorCallback);
    };

    this.fids_to_orthologs = function (fids, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.fids_to_orthologs",
            [fids], 1, _callback, _errorCallback);
    };

    this.fids_to_ec = function (fids, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.fids_to_ec",
            [fids], 1, _callback, _errorCallback);
    };

    this.fids_to_go = function (fids, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.fids_to_go",
            [fids], 1, _callback, _errorCallback);
    };

    this.fid_to_neighbors = function (id, thresh, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.fid_to_neighbors",
            [id, thresh], 1, _callback, _errorCallback);
    };

    this.fidlist_to_neighbors = function (fids, thresh, _callback, _errorCallback) {
        return json_call_ajax("ProteinInfo.fidlist_to_neighbors",
            [fids, thresh], 1, _callback, _errorCallback);
    };

    /*
     * JSON call using jQuery method.
     */
    function json_call_ajax(method, params, numRets, callback, errorCallback) {
        var deferred = $.Deferred();

        if (typeof callback === 'function') {
           deferred.done(callback);
        }

        if (typeof errorCallback === 'function') {
           deferred.fail(errorCallback);
        }

        var rpc = {
            params : params,
            method : method,
            version: "1.1",
            id: String(Math.random()).slice(2),
        };
        
        var beforeSend = null;
        var token = (_auth_cb && typeof _auth_cb === 'function') ? _auth_cb()
            : (_auth.token ? _auth.token : null);
        if (token != null) {
            beforeSend = function (xhr) {
                xhr.setRequestHeader("Authorization", _auth.token);
            }
        }

        jQuery.ajax({
            url: _url,
            dataType: "text",
            type: 'POST',
            processData: false,
            data: JSON.stringify(rpc),
            beforeSend: beforeSend,
            success: function (data, status, xhr) {
                var result;
                try {
                    var resp = JSON.parse(data);
                    result = (numRets === 1 ? resp.result[0] : resp.result);
                } catch (err) {
                    deferred.reject({
                        status: 503,
                        error: err,
                        url: _url,
                        resp: data
                    });
                    return;
                }
                deferred.resolve(result);
            },
            error: function (xhr, textStatus, errorThrown) {
                var error;
                if (xhr.responseText) {
                    try {
                        var resp = JSON.parse(xhr.responseText);
                        error = resp.error;
                    } catch (err) { // Not JSON
                        error = "Unknown error - " + xhr.responseText;
                    }
                } else {
                    error = "Unknown Error";
                }
                deferred.reject({
                    status: 500,
                    error: error
                });
            }
        });
        return deferred.promise();
    }
}


