# rogue_meraki_sdk_generator.py
A Python 3 script that generates a Meraki Dashboard API SDK module for Python 3.

**THIS IS NOT THE OFFICIAL MERAKI DASHBOARD API SDK**

The intent of the generated module is to provide an easy and reliable way to interact with endpoints that are not part of the latest release of the official Meraki Python SDK using Python 3. These types of endpoints are mostly Early Access (alpha/beta) ones, available to members of the Developer Early Access Program.

For all other uses, please use the official Meraki Dashboard API Python SDK instead:
https://github.com/meraki/dashboard-api-python

The script works by pulling the OpenAPI spec of a Meraki dashboard organization and generating code for every endpoint available to the chosen organization. If special endpoints, like aplha/beta ones, are enabled for the source organization, they will be included in the output module as well.

# Running the script
* Install Python 3 if you have not done so already. If installing on Windows, it is recommended to select the "Add to PATH" option during installation
* Install the requests Python 3 module. The easiest way to do this is to run:
```
Windows:
pip install requests

Linux/Mac:
pip3 install requests
```

* Run the script, by running the following command, replacing <api_key> with your Dashboard API key. If you prefer, you can also omit parameter "-k" altogether, and have the script pull your key from an environment variable named "MERAKI_DASHBOARD_API_KEY" instead:
```
Windows:
python rogue_meraki_sdk_generator.py -k <api_key>

Linux/Mac:
python3 rogue_meraki_sdk_generator.py -k <api_key>

Example:
python rogue_meraki_sdk_generator.py -k 1234

```

* By default, the script will pull the list of available endpoints from the first organization accessible by your administrator account. If you want to specify which organization to pick, use this form instead, replacing `<api_key>` with your Meraki Dashboard API key and `<org_name>` with the name of the organization you want the script to use:
```
Windows:
python rogue_meraki_sdk_generator.py -k <api_key> -o <org_name>

Linux/Mac:
python3 rogue_meraki_sdk_generator.py -k <api_key> -o <org_name>

Example:
python rogue_meraki_sdk_generator.py -k 1234 -o "Big Industries Inc"
```

# Using the generated module
The script creates a Meraki Dashboard API module for Python 3 as a single file in the same directory as the script itself. By default, the output file will be named `meraki_rogue_<timestamp>.py`.

The SDK requires the requests module: https://docs.python-requests.org/en/latest/
    
How to use the output module:
1. Rename the output module file to meraki_rogue.py
2. Copy the module into the same directory as your script
3. In your script, add the following line to import the module:
```
    import meraki_rogue
```
4. You can now use the endpoint methods included in the module. For example, to get a list of the organizations
   your API key can access, add the following line to your code, assuming your API key is 1234:
```
    success, errors, response = meraki_rogue.getOrganizations(1234)
```
    
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
```
success, errors, response = meraki_rogue.<operationId>(<apiKey><url_parameters><query_options><request_body>)
```    

The endpoints return a tuple of 3 values:
```
success : Boolean, whether the operation was successful or not
errors  : If the request was unsuccessful and returned error text, it will be here
response: If the request was successful and JSON payload was returned as a response body, it will be here
```
    
Some endpoints can take query parameters or a request body as input. They are passed to the endpoint method
as dicttionaries, via the "query" and "body" parameters.

Example of calling a method with query parameters:
```
apiKey = "1234"
organizationId = "4567"
query = {"timespan": 100000}
success, errors, response = meraki_rogue.getOrganizationClientsBandwidthUsageHistory(apiKey, organizationId, query)
```

Example of calling a method with a request body:
```
apiKey = "1234"
organizationId = "4567"
body = {"name": "Cloned Organization"}
success, errors, response = meraki_rogue.cloneOrganization(apiKey, organizationId, body)
```    

# Copying code into your script

Alternatively, instead of importing the whole module, you can copy the endpoints you are going to use in your script directly. To do this:
* Copy the module's core functions and definitions: Find these lines in the code of the output module and copy everything between them:
```
# --- MODULE CORE START ---

# --- MODULE CORE END ---
```
* Copy the individual endpoint methods that you are going to use. You can find them in the code of the module after line:
```
# --- ENDPOINT METHODS BELOW ---
```

# Useful links
* The official Meraki API developer page: https://developer.cisco.com/meraki
* The official Meraki Dashboard API SDK for Python 3: https://github.com/meraki/dashboard-api-python
* Meraki Dashboard API quick reference with alpha/beta endpoint highlighting: https://github.com/mpapazog/meraki-diff-docs
* Custom Postman collection that includes alpha/beta endpoints: https://github.com/meraki/automation-scripts/blob/master/postman_collection_generator.py
* Node.js module generator with alpha/beta endpoint support: https://github.com/meraki/automation-scripts/tree/master/nodejs_sdk_builder
