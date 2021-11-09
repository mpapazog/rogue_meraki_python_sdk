readMe = '''
This script generates a Python module that can be used to interact with the Meraki Dashboard API.

*** THIS IS NOT THE OFFICIAL MERAKI DASHBOARD API PYTHON SDK ***

The intent of the generated module is to provide an easy and reliable way to interact with endpoints that are not
part of the latest release of the official Meraki Python SDK using Python 3. These types of endpoints are mostly
Early Access (alpha/beta) ones, available to members of the Developer Early Access Program.

For all other uses, please use the official Meraki Dashboard API Python SDK instead:
https://github.com/meraki/dashboard-api-python

The script works by pulling the OpenAPI spec of a Meraki dashboard organization and generating code for every
endpoint available to the chosen organization. If special endpoints, like aplha/beta ones, are enabled for the
source organization, they will be included in the output module as well.


--- How to use this script ---

Syntax, Windows:
    python rogue_meraki_sdk_generator.py [-k <api_key>] [-o <org_name>] [-f <file_name>]
    
Syntax, Linux and Mac:
    python3 rogue_meraki_sdk_generator.py [-k <api_key>] [-o <org_name>] [-f <file_name>]
    
Optional arguments:
    -k <api_key>        Your Meraki Dashboard API key. If omitted, the script will try to use one stored in
                        OS environment variable MERAKI_DASHBOARD_API_KEY
    -o <org_name>       The name of the organization to pull the OpenAPI spec from. This parameter can be 
                        omitted if your API key can only access one org
    -f <file_name>      The name of the output file. If omitted, "meraki_rogue_<timestamp>.py" will be used
                        as default
                        
Example, generate a SDK for all endpoints available to organization with name "Big Industries Inc"
    python rogue_meraki_sdk_generator.py -k 1234 -o "Big Industries Inc"
    
Required Python 3 modules:
    requests

To install these Python 3 modules via pip you can use the following commands:
    pip install requests

Depending on your operating system and Python environment, you may need to use commands 
"python3" and "pip3" instead of "python" and "pip".


--- How to use the generated module ---

1. Rename the output module file to meraki_rogue.py
2. Copy the module into the same directory as your script
3. In your script, add the following line to import the module:
    import meraki_rogue
4. You can now use the endpoint methods included in the module. For example, to get a list of the organizations
   your API key can access, add the following line to your code, assuming your API key is 1234:
    success, errors, response = meraki_rogue.getOrganizations(1234)
    
To find the correct method for the endpoint you want to use, first find its operationId or resource path. 
Some ways to find those are:
* The official Meraki Dashboard API documentation page: 
    https://developer.cisco.com/meraki/api-v1/
* The API documentation page built into your Meraki dashboard, via the "Help > API docs" menu item
* This custom API documentation server that includes alpha/beta endpoints: 
    https://github.com/mpapazog/meraki-diff-docs
* This custom Postman collection that includes alpha/beta endpoints: 
    https://github.com/meraki/automation-scripts/blob/master/postman_collection_generator.py
    
You can then open the module in your text editor and use its search functionality to find the endpoint
method you need. The method's opening comments will include info about its parameters.

In general, calling any of the endpoints is structured as follows:
    success, errors, response = meraki_rogue.<operationId>(<apiKey><url_parameters><query_options><request_body>)
    
The endpoints return a tuple of 3 values:
    success : Boolean, whether the operation was successful or not
    errors  : If the request was unsuccessful and returned error text, it will be here
    response: If the request was successful and JSON payload was returned as a response body, it will be here
    
Some endpoints can take query parameters or a request body as input. They are passed to the endpoint method
as dicttionaries, via the "query" and "body" parameters.

Example of calling a method with query parameters:
    apiKey = "1234"
    organizationId = "4567"
    query = {"timespan": 100000}
    success, errors, response = meraki_rogue.getOrganizationClientsBandwidthUsageHistory(apiKey, organizationId, query)

Example of calling a method with a request body:
    apiKey = "1234"
    organizationId = "4567"
    body = {"name": "Cloned Organization"}
    success, errors, response = meraki_rogue.cloneOrganization(apiKey, organizationId, body)
    
'''

import os, sys, getopt, time, datetime

from urllib.parse import urlencode
from requests import Session, utils

class NoRebuildAuthSession(Session):
    def rebuild_auth(self, prepared_request, response):
        """
        This method is intentionally empty. Needed to prevent auth header stripping on redirect. More info:
        https://stackoverflow.com/questions/60358216/python-requests-post-request-dropping-authorization-header
        """

API_MAX_RETRIES             = 3
API_CONNECT_TIMEOUT         = 60
API_TRANSMIT_TIMEOUT        = 60
API_STATUS_RATE_LIMIT       = 429
API_RETRY_DEFAULT_WAIT      = 3

#Set to True or False to enable/disable console logging of sent API requests
FLAG_REQUEST_VERBOSE        = True

API_BASE_URL                = "https://api.meraki.com/api/v1"
API_KEY_ENV_VAR_NAME        = "MERAKI_DASHBOARD_API_KEY"

TEMPLATE_FILE_SDK_CORE  = "core.template"
TEMPLATE_FILE_ENDPOINT  = "endpoint.template"

def merakiRequest(p_apiKey, p_httpVerb, p_endpoint, p_additionalHeaders=None, p_queryItems=None, 
        p_requestBody=None, p_verbose=False, p_retry=0):
    #returns success, errors, responseHeaders, responseBody
    
    if p_retry > API_MAX_RETRIES:
        if(p_verbose):
            print("ERROR: Reached max retries")
        return False, None, None, None
        
    bearerString = "Bearer " + str(p_apiKey)
    headers = {"Authorization": bearerString}
    if not p_additionalHeaders is None:
        headers.update(p_additionalHeaders)
        
    query = ""
    if not p_queryItems is None:
        query = "?" + urlencode(p_queryItems, True)
    url = API_BASE_URL + p_endpoint + query
    
    verb = p_httpVerb.upper()
    
    session = NoRebuildAuthSession()
    
    verbs   = {
        'DELETE'    : { 'function': session.delete, 'hasBody': False },
        'GET'       : { 'function': session.get,    'hasBody': False },
        'POST'      : { 'function': session.post,   'hasBody': True  },
        'PUT'       : { 'function': session.put,    'hasBody': True  }
    }

    try:
        if(p_verbose):
            print(verb, url)
            
        if verb in verbs:
            if verbs[verb]['hasBody'] and not p_requestBody is None:
                r = verbs[verb]['function'](
                    url,
                    headers =   headers,
                    json    =   p_requestBody,
                    timeout =   (API_CONNECT_TIMEOUT, API_TRANSMIT_TIMEOUT)
                )
            else: 
                r = verbs[verb]['function'](
                    url,
                    headers =   headers,
                    timeout =   (API_CONNECT_TIMEOUT, API_TRANSMIT_TIMEOUT)
                )
        else:
            return False, None, None, None
    except:
        return False, None, None, None
    
    if(p_verbose):
        print(r.status_code)
    
    success         = r.status_code in range (200, 299)
    errors          = None
    responseHeaders = None
    responseBody    = None
    
    if r.status_code == API_STATUS_RATE_LIMIT:
        retryInterval = API_RETRY_DEFAULT_WAIT
        if "Retry-After" in r.headers:
            retryInterval = r.headers["Retry-After"]
        if "retry-after" in r.headers:
            retryInterval = r.headers["retry-after"]
        
        if(p_verbose):
            print("INFO: Hit max request rate. Retrying %s after %s seconds" % (p_retry+1, retryInterval))
        time.sleep(int(retryInterval))
        success, errors, responseHeaders, responseBody = merakiRequest(p_apiKey, p_httpVerb, p_endpoint, p_additionalHeaders, 
            p_queryItems, p_requestBody, p_verbose, p_retry+1)
        return success, errors, responseHeaders, responseBody        
            
    try:
        rjson = r.json()
    except:
        rjson = None
        
    if not rjson is None:
        if "errors" in rjson:
            errors = rjson["errors"]
            if(p_verbose):
                print(errors)
        else:
            responseBody = rjson  

    if "Link" in r.headers:
        parsedLinks = utils.parse_header_links(r.headers["Link"])
        for link in parsedLinks:
            if link["rel"] == "next":
                if(p_verbose):
                    print("Next page:", link["url"])
                splitLink = link["url"].split("/api/v1")
                success, errors, responseHeaders, nextBody = merakiRequest(p_apiKey, p_httpVerb, splitLink[1], 
                    p_additionalHeaders=p_additionalHeaders, 
                    p_requestBody=p_requestBody, 
                    p_verbose=p_verbose)
                if success:
                    if not responseBody is None:
                        responseBody = responseBody + nextBody
                else:
                    responseBody = None
    
    return success, errors, responseHeaders, responseBody
    
    
def getOrganizations(p_apiKey):
    endpoint = "/organizations"
    success, errors, headers, response = merakiRequest(p_apiKey, "GET", endpoint, p_verbose=FLAG_REQUEST_VERBOSE)    
    return success, errors, response    
    
    
def getOrganizationOpenapiSpec(p_apiKey, p_organizationId):
    endpoint = "/organizations/%s/openapiSpec" % p_organizationId
    success, errors, headers, response = merakiRequest(p_apiKey, "GET", endpoint, p_verbose=FLAG_REQUEST_VERBOSE)    
    return success, errors, response
    
    
def log(text, filePath=None):
    logString = "%s -- %s" % (datetime.datetime.now(), text)
    print(logString)
    if not filePath is None:
        try:
            with open(filePath, "a") as logFile:
                logFile.write("%s\n" % logString)
        except:
            log("ERROR: Unable to append to log file")


def killScript(reason=None):
    if reason is None:
        print(readMe)
        sys.exit()
    else:
        log("ERROR: %s" % reason)
        sys.exit()
        
        
def generateOutputFileName(argFile):
    if argFile is None:
        timestampIso = datetime.datetime.now().isoformat()[:19]
        timestampFileNameFriendly = timestampIso.replace(":",".").replace("T","_")
        name = "meraki_rogue_" + timestampFileNameFriendly + ".py"
        return name
    else:
        return argFile
               
        
def loadFile(filename):
    with open(filename, 'r') as file:
        data = file.read()
    return data
    
  
def dashifyOperationId(operationId):
    result = ""

    for char in operationId:
        if char.isupper():
            result += "-%s" % char.lower()
        else:
            result += char

    return result
    

def getApiKey(argument):
    if not argument is None:
        return str(argument)
    apiKey = os.environ.get(API_KEY_ENV_VAR_NAME, None) 
    if apiKey is None:
        killScript()
    else:
        return apiKey
        
        
def main(argv):    
    arg_apiKey      = None
    arg_orgName     = None
    arg_fileName    = None
    
    try:
        opts, args = getopt.getopt(argv, 'k:o:f:h:')
    except getopt.GetoptError:
        killScript()
        
    for opt, arg in opts:
        if opt == '-k':
            arg_apiKey      = str(arg)
        elif opt == '-o':
            arg_orgName     = str(arg)
        elif opt == '-f':
            arg_fileName    = str(arg)
        elif opt == '-h':
            killScript()
            
    apiKey = getApiKey(arg_apiKey)   
    
    outputFileName      = generateOutputFileName(arg_fileName)
    coreTemplate        = loadFile(TEMPLATE_FILE_SDK_CORE)
    endpointTemplate    = loadFile(TEMPLATE_FILE_ENDPOINT)
    
    success, errors, allOrgs = getOrganizations(apiKey)
    
    if allOrgs is None:
        killScript("Unable to fetch organizations for that API key")
    
    organizationId      = None
    organizationName    = ""
    
    if arg_orgName is None:
        if len(allOrgs) == 1:
            organizationId      = allOrgs[0]['id']
            organizationName    = allOrgs[0]['name']
        else:
            killScript("Organization name required for this API key")             
    else:
        for org in allOrgs:
            if org["name"] == arg_orgName:
                organizationId      = org['id']
                organizationName    = org['name']
                break
    if organizationId is None:
        killScript("No matching organizations")
                                
    success, errors, openApiSpec = getOrganizationOpenapiSpec(apiKey, organizationId)
        
    outputAllEndpoints = ""
    
    for path in openApiSpec["paths"]:
        for method in openApiSpec["paths"][path]:   
            operationId = openApiSpec["paths"][path][method]["operationId"]
            operationIdDash = dashifyOperationId(operationId)
            description = openApiSpec["paths"][path][method]["description"].replace("\n", " ")
            pathVars = []
            query = []
            body = []
            
            if "parameters" in openApiSpec["paths"][path][method]:
                for param in openApiSpec["paths"][path][method]["parameters"]:
                    if param["in"] == "path":
                        pathVars.append({"name": param["name"]})
                    elif param["in"] == "query":
                        query.append( { "name": param["name"], "description": param["description"].replace("\n", " "), "type": param["type"] } )
                    elif param["in"] == "body":
                        for bodyItem in param["schema"]["properties"]:
                            body.append( { "name": bodyItem, 
                                "description": param["schema"]["properties"][bodyItem]["description"].replace("\n", " "), 
                                "type": param["schema"]["properties"][bodyItem]["type"] } )
                    
            
            outputEndpoint = endpointTemplate
            
            outputEndpoint = outputEndpoint.replace("###ENDPOINT_TITLE", "# %s\n#\n# Description: %s" %(operationId, description));          
            outputEndpoint = outputEndpoint.replace("###ENDPOINT_VERB_URI", "\n# Endpoint: %s %s" %(method.upper(), path));          
            outputEndpoint = outputEndpoint.replace("###DOCS_LINK", "\n#\n# Endpoint documentation: https://developer.cisco.com/meraki/api-v1/#!%s" % operationIdDash);          
            outputEndpoint = outputEndpoint.replace("###ENDPOINT_ID", operationId);
            outputEndpoint = outputEndpoint.replace("###VERB", '"%s"' % method);
            
            resourcePath = '"%s"' % path
            
            paramString = ""
                
            if len(pathVars) > 0:
                for p in pathVars:
                    paramString += ", %s" % p["name"]
                    resourcePath = resourcePath.replace( "{%s}" % p["name"], '" + str(%s) + "' % p["name"])
                
            if resourcePath[-5:] == ' + ""':
                resourcePath = resourcePath[:-5]
            outputEndpoint = outputEndpoint.replace("###RESOURCE_PATH", resourcePath);
                
            queryDocs   = ""
            bodyDocs    = ""
            
            queryArgument = ""
            if len(query) > 0:            
                paramString += ", query=None"
                queryArgument = "p_queryItems=query, "
                queryDocs = "\n#\n# Query parameters:"
                for q in query:
                    queryDocs += "\n#     %s: %s. %s" % (q["name"], q["type"].capitalize(), q["description"])
            else:
                outputEndpoint = outputEndpoint.replace("/* QUERY PARAM */", '');
                
            outputEndpoint = outputEndpoint.replace("###QUERY_FORMAT", queryDocs);
                
            bodyArgument = ""
            if len(body) > 0:                 
                paramString += ", body=None"
                bodyArgument = "p_requestBody=body, "
                bodyDocs = "\n#\n# Request body schema:"
                for b in body:
                    bodyDocs += "\n#     %s: %s. %s" % (b["name"], b["type"].capitalize(), b["description"])
                    
            outputEndpoint = outputEndpoint.replace("###PARAMETERS",    paramString);                
            outputEndpoint = outputEndpoint.replace("###BODY_FORMAT",   bodyDocs);            
            outputEndpoint = outputEndpoint.replace("###QUERY",         queryArgument);
            outputEndpoint = outputEndpoint.replace("###BODY",          bodyArgument);
            
            outputAllEndpoints += outputEndpoint;
                       
    outputTotal = coreTemplate
    
    outputTotal = outputTotal.replace("###DATE", datetime.datetime.now().isoformat());
    outputTotal = outputTotal.replace("###ORG_NAME", organizationName);
    outputTotal = outputTotal.replace("###FILENAME", outputFileName);
    outputTotal = outputTotal.replace("###ENDPOINTS", outputAllEndpoints);
    
    f = open(outputFileName, 'w')
    f.write(outputTotal)
    f.close()
        
    log("File %s written" % outputFileName)
    
if __name__ == '__main__':
    main(sys.argv[1:])
