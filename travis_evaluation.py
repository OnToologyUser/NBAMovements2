from github import Github
import os
import fnmatch
import re
from SPARQLWrapper import SPARQLWrapper, JSON, XML, RDF
import glob
import requests
import myconf
import rdfxml  as rdfxml
from xml.etree import ElementTree as ElementTree
import rdflib
import types


def main():
	global flag 
	flag = False
	#GitHub authentication
	client_token = os.environ['github_token']
	g = Github(client_token)
	
	for repo in g.get_user().get_repos():
	 if repo.has_in_collaborators('OnToologyUser'):
	  #create labels for acceptance test notifications
	  create_labels(repo)
	  ##########TESTS#########
	  
	  ###Acceptance test
	  print 'Starting acceptance test...'
	  list_of_files=[]
	  for root, dirnames, filenames in os.walk('./'):
    		for filename in fnmatch.filter(filenames, '*.rq'):
        		list_of_files.append(os.path.join(root, filename))
          
	  #list_of_files = glob.glob('./*.rq',recursive=True)
	  close_old_acc_issues_in_github(repo)
	   # Each file has a requirement
	  s = "The ontology created has not passed the acceptance test:\n" 
	  i = 0
	  flag = False
	  for file in list_of_files:
	    #Reading the results given by the user
	    list_elements_results,list_elements_results_type, num_res,type_res,list_results_user,priority = read_query(file)

	    if not list_elements_results:
	    	i += 1
	    	s += "%d. " % (i) + 'The ontology can not answer to the requirement with ID ' + os.path.splitext(os.path.basename(file))[0].split("_")[1]
	    	if priority != 0:
	    		s +='. Priority of the requirement: ' + priority +'.\n' 
	    	else:
	    		s+= '\n'
	    	flag = True
	    	print 'not'
	    	print s
	    	#repo.create_issue('Acceptance test notification', s , labels = ['Acceptance test bug'])
	    else:
	    	s,i = checking_results(num_res,type_res, list_elements_results, list_elements_results_type,list_results_user,file,priority,i,s,repo)
	  
	  if flag == True:
	  	print 'creating acceptance test issue...'
	  	repo.create_issue('Acceptance test notification', s , labels = ['Acceptance test bug'])     	
	    	
	  ###Unit test
	 # ont_files = glob.glob('./*.owl')
	 # print 'Starting unit test with OOPS!...'
	 # for file in ont_files:
	#	    f = open(file, 'r')
	#	    ont = f.read()
	#	    issues_s = get_pitfalls(ont)
	#	    close_old_oops_issues_in_github(repo, file)
	#	    nicer_oops_output(issues_s,file,repo)
	    
  
##Function to read the cqs and the results given by the user

def read_query(req_file):
    priority = 0
    req = open(req_file, 'r')
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    query_c =  req.read()
    query = query_c.split('#Results')
    #Reading results
    query_aux = query[1].split('#Type of the results')
    num_res = query_aux[0].replace('#Number of results','').replace("\n","")
    type_res = query_aux[1].split('#List of results')[0]
    list_type_res = type_res.strip()
    list_type_res = list_type_res.replace("\n","").split(",")
    results_user = query_aux[1].split('#List of results')[1]
    if '#Priority' in results_user:
    	results_user_prior_split = results_user.split('#Priority')
    
	print results_user_prior_split[0].strip().replace('\n','')
    	#if the requirement has priority
    	#if results_user_prior_split[0].replace(" ","").replace('\n','') != 'false':
	results_user = results_user_prior_split[0]
        priority  = results_user_prior_split[1].strip().replace('\n','')
    list_elements_result = results_user.strip().split("\n")
    list_aux = []
    for element in list_elements_result:
    	if element != '':
    		element_aux = element.split(",")
    		list_aux.append(element_aux)
 
    
    graph = rdflib.Graph()
    name_file = os.path.splitext(os.path.basename(req_file))[0].split("_")[0] + '.owl'
    print name_file
    graph.parse(name_file) 
    results = graph.query(query[0])
    results_list = []
    results_list_type = []
    for row in graph.query(query[0]):
    	row_element = []
    	row_element_type = []
	if type(row)  != types.BooleanType:
	    for element in row: 
	    		row_element.append(str(element))
	    		row_element_type.append(type(element).__name__)
	else:
		row_element.append(str(row))
	    	row_element_type.append('Boolean')

        results_list_type.append(row_element_type)
        results_list.append(row_element)
    print req_file
    print '==============='
    print  results_list
    print '=============='
   
    req.close()
    return results_list,results_list_type, num_res,list_type_res,list_aux,priority
    
##Function to check if the results obtained by the system are correct
 
def checking_results(num_res,type_res, list_elements_results, list_elements_results_type, list_results_user,file,priority,i,s,repo):
  	global flag
  	error_list = []
    	#check if the number of results are the same that the user expected
    	if  ">" in num_res:
    		if len(list_elements_results) < int(num_res.replace('>','')):
    			error_list.append("len")
    	   		i += 1
    		 	s += "%d. " % (i) + 'Error with the requirement with ID ' + os.path.splitext(os.path.basename(file))[0].split("_")[1]
    		 	if priority != 0:
	    			s +='. Priority of the requirement: ' + priority +'.\n'
	    		else:
	    			s+= '\n'
    		 	
    		 	s += "    - The ontology return fewer results than expected. Expected: "+str(num_res)+ " but was: "+str(len(list_elements_results))+".\n"    		 
    		 	flag = True
    	elif "<" in num_res:
    		if len(list_elements_results) > int(num_res.replace('<','')):
    			error_list.append("len")
    	   		i += 1
    		 	s += "%d. " % (i) + 'Error with the requirement with ID  ' + os.path.splitext(os.path.basename(file))[0].split("_")[1]
    	 	 	if priority != 0:
	    			s +='. Priority of the requirement: ' + priority +'.\n'
	    		else:
	    			s+= '\n'
    	 	 	flag = True
    	 	 	s += "    - The ontology return more results than expected. Expected: "+str(num_res)+ " but was: "+str(len(list_elements_results))+".\n"
    	else:
    		 if len(list_elements_results) != int(num_res.replace('=','')):
    		 	error_list.append("len")
    	   		i += 1
    		 	s += "%d. " % (i) + 'Error with the requirement with ID ' + os.path.splitext(os.path.basename(file))[0].split("_")[1]
    	 	 	if priority != 0:
	    			s +='. Priority of the requirement: ' + priority +'.\n'
	    		else:
	    			s+= '\n'
    	 	 	s += "    - The ontology did not return the number of results expected. Expected: "+str(num_res)+ " but was: "+str(len(list_elements_results))+".\n"
    	 	 	flag = True
    	 	
        #check if the user examples are contained in the results 
        print '----SAMPLES----'
        isinside = False
        for result in list_results_user:
        		
             		for elem in list_elements_results:
             			print result
             			print elem
        			if all(x in result for x in elem):
        				
					isinside = True
		 	
    	   		if isinside == False:
    	   			if len(error_list) == 0:
    	   					i += 1
    	   					s += "%d. " % (i) + 'Error with the requirement with ID  ' + os.path.splitext(os.path.basename(file))[0].split("_")[1]
   	   					if priority != 0:
	    						s +='. Priority of the requirement: ' + priority +'.\n'
	    					else:
	    						s+= '.\n'
   	   					error_list.append("list")
      				s += '    - The ontology did not return the results that the user expected. Expected: ['+', '.join(result)
      				s+='] in the list of results.\n'
      				flag = True
    				break

        #check if the types are the same that the user expected
        for result in list_elements_results_type: 
        	aux = False
        	j = 0
        	#list_tags = []
           	for elem in result: 
           		#tag = list(elem.iter())[1].tag
        		#list_tags.append(tag)
        		if not type_res[j]  in elem:
    	   			if len(error_list) == 0:
    	   				error_list.append("type")
    	   				i += 1
    	   				s += "%d. " % (i) + 'Error with the requirement with ID ' + os.path.splitext(os.path.basename(file))[0].split("_")[1]
    	   				if priority != 0:
	    					s +='. Priority of the requirement: ' + priority +'.\n'
	    				else:
	    					s+= '.\n'
    	   		
    	   			aux = True
    	   			
    	   		j+=1 
    		if aux == True:
    			flag = True
	  		s += "    - The results returned by the ontology has not the data type expected by the user. Expected: ["+', '.join(type_res)+"] but was: ["+', '.join(result)+"]\n"
	  		break
	#if there are errors
	#if len(error_list) > 0:
 	#	repo.create_issue('Acceptance test notification', s , labels = ['Acceptance test bug'])   
 	return s,i
     
##Function to create issues labels in github

def create_labels(repo):
   flag_acc = False
   flag_unit = False
   flag_inference = False
   flag_model = False
   flag_metadata = False
   flag_lang = False
   flag_en = False
   flag_important = False
   flag_critical = False
   flag_minor = False
   for label in repo.get_labels():
    if label.name == "Acceptance test bug":
      flag_acc = True
    elif label.name == "Unit test bug":
      flag_unit =True
    elif label.name == "Inference":
      flag_inference =True
    elif label.name == "Modeling":
      flag_model = True
    elif label.name == "Language":
      flag_lang = True
    elif label.name == "Metadata":
      flag_metadata = True
    elif label.name == "Important":
      flag_important = True
    elif label.name == "Critical":
      flag_critical = True
    elif label.name == "Minor":
      flag_minor = True
      
   if flag_acc == False:  
    repo.create_label("Acceptance test bug", "F50511")
   if flag_unit == False: 
    repo.create_label("Unit test bug", "F50511")
   if flag_inference == False:
    repo.create_label("Inference",  "c2e0c6")
   if flag_model == False:
    repo.create_label("Modeling",  "d4c5f9")
   if flag_lang == False:
    repo.create_label("Language",  "FFCCE5")
   if flag_metadata == False:
    repo.create_label("Metadata", "c5def5")
   if flag_important == False:
    repo.create_label("Important", "FFB266")
   if flag_critical == False:
    repo.create_label("Critical", "F50511")
   if flag_minor == False:
    repo.create_label("Minor", "FFFFCC") 
    
##Functions to obtain oops pitfalls and to create github issues
    
def get_pitfalls(ont_file):
    url = 'http://oops-ws.oeg-upm.net/rest'
    xml_content = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OOPSRequest>
          <OntologyUrl></OntologyUrl>
          <OntologyContent>%s</OntologyContent>
          <Pitfalls></Pitfalls>
          <OutputFormat></OutputFormat>
    </OOPSRequest>
    """ % (ont_file)
    headers = {'Content-Type': 'application/xml',
               'Connection': 'Keep-Alive',
               'Content-Length': len(xml_content),

               'Accept-Charset': 'utf-8'
               }
    print "will call oops webservice"

    oops_reply = requests.post(url, data=xml_content, headers = headers)
   # print "will get oops text reply"
    oops_reply = oops_reply.text
   # print 'oops reply is: <<' + oops_reply + '>>' 
    #print '<<<end of oops reply>>>'
    
    if oops_reply[:50] == '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">':
        if '<title>502 Proxy Error</title>' in oops_reply:
            raise Exception('Ontology is too big for OOPS')
        else:
            raise Exception('Generic error from OOPS')
    issues_s = output_parsed_pitfalls(ont_file, oops_reply)
    return issues_s
    
def output_parsed_pitfalls(ont_file, oops_reply):
    issues, interesting_features = parse_oops_issues(oops_reply)
    s = ""
    for i in issues:
        for intfea in interesting_features:
            if intfea in issues[i]:
                val = issues[i][intfea].split('^^')[0]
                key = intfea.split("#")[-1].replace('>', '')
                s += key + ": " + val + "\n"
        s + "\n"
        s += 20 * "="
        s += "\n"
    print 'oops issues gotten'
    return s
    
def parse_oops_issues(oops_rdf):
    p = rdfxml.parseRDF(oops_rdf)
    raw_oops_list = p.result
    oops_issues = {}

    # Filter #1
    # Construct combine all data of a single elements into one json like format
    for r in raw_oops_list:
        if r['domain'] not in oops_issues:
            oops_issues[r['domain']] = {}
        oops_issues[r['domain']][r['relation']] = r['range']

    # Filter #2
    # get rid of elements without issue id
    oops_issues_filter2 = {}
    for i in oops_issues:
        if '#' not in i:
            oops_issues_filter2[i] = oops_issues[i]

    # Filter #3
    # Only include actual issues (some data are useless to us)
    detailed_desc = []
    oops_issues_filter3 = {}
    for i in oops_issues_filter2:
        if '<http://www.oeg-upm.net/oops#hasNumberAffectedElements>' in oops_issues_filter2[i]:
            oops_issues_filter3[i] = oops_issues_filter2[i]
    # Filter #4
    # Only include data of interest about the issue
    oops_issues_filter4 = {}
    issue_interesting_data = [
        '<http://www.oeg-upm.net/oops#hasName>',
        '<http://www.oeg-upm.net/oops#hasCode>',
        '<http://www.oeg-upm.net/oops#hasDescription>',
        '<http://www.oeg-upm.net/oops#hasNumberAffectedElements>',
        '<http://www.oeg-upm.net/oops#hasImportanceLevel>',
        #'<http://www.oeg-upm.net/oops#hasAffectedElement>',
        '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>',
    ]
    for i in oops_issues_filter3:
        oops_issues_filter4[i] = {}
        for intda in issue_interesting_data:
            if intda in oops_issues_filter3[i]:
                oops_issues_filter4[i][intda] = oops_issues_filter3[i][intda]
    return oops_issues_filter4, issue_interesting_data
    
def nicer_oops_output(issues,ont_file,repo):
    sugg_flag = '<http://www.oeg-upm.net/oops#suggestion>'
    pitf_flag = '<http://www.oeg-upm.net/oops#pitfall>'
    warn_flag = '<http://www.oeg-upm.net/oops#warning>'
    num_of_suggestions = issues.count(sugg_flag)
    num_of_pitfalls = issues.count(pitf_flag)
    num_of_warnings = issues.count(warn_flag)
    #create suggestions issue
    if num_of_suggestions > 0 or num_of_pitfalls > 0 :
     p = " OOPS! has encountered some pitfalls related to " 
    
     nodes = issues.split("====================")
     warn = []
     suggs = []
     m_pitf = []
     inf_pitf = []
     mod_pitf = []
     met_pitf = []
     lang_pitf = []
     inf_pitf_i = []
     mod_pitf_i = []
     met_pitf_i = []
     lang_pitf_i = []
     desc = ""
     labels = []
     for node in nodes[:-1]:
     	labels = []
        attrs = node.split("\n")
        if pitf_flag in node:
          flag_i = False
          flag_mo = False
          flag_me = False
          flag_l = False
          for attr in attrs:
           #catching the name of the pitfall
           if 'hasName' in attr: 
              desc = attr.replace('hasName: ', '')
           #minor pitfalls
           if  'hasImportanceLevel: \"Minor\"' in attr and desc != "":
                m_pitf.append(desc)
                break
           #critical-important pitfalls     
           if 'hasCode' in attr:
            attr_n = attr.replace('hasCode: ', '')
            #inference pitfalls
            if attr_n == '\"P06\"' or attr_n == '\"P19\"' or attr_n == '\"P29\"' or attr_n == '\"P28\"' or attr_n == '\"P31\"' or attr_n == '\"P05\"' or attr_n == '\"P27\"' or attr_n == '\"P15\"' or attr_n == '\"P01\"' or attr_n == '\"P16\"' or attr_n == '\"P18\"' or attr_n == '\"P11\"' or attr_n == '\"P12\"' or attr_n == '\"P30\"':
              inf_pitf.append(desc)
              flag_i = True
            #modeling pitfalls   
            elif attr_n == '\"P03\"' or attr_n == '\"P14\"' or attr_n == '\"P24\"' or attr_n == '\"P25\"' or attr_n == '\"P26\"' or attr_n == '\"P17\"' or attr_n == '\"P23\"' or attr_n == '\"P10\"':
               mod_pitf.append(desc)
               flag_mo = True
            #metadata pitfalls  
            elif attr_n == '\"P39\"' or attr_n == '\"P40\"' or attr_n == '\"P38\"' or attr_n == '\"P41\"':
                met_pitf.append(desc)
                flag_me = True
            #ontology language pitfalls   
            elif attr_n == '\"P34\"' or attr_n == '\"P35\"':
              lang_pitf.append(desc)
              flag_l = True
              
           #importance for each pitfall  
           if 'hasImportanceLevel' in attr:
            if flag_i == True:
             inf_pitf_i.append(attr.replace('hasImportanceLevel: ', ''))
             break
            elif flag_mo ==True:
              mod_pitf_i.append(attr.replace('hasImportanceLevel: ', ''))
              break   
            elif flag_me ==True:
              met_pitf_i.append(attr.replace('hasImportanceLevel: ', ''))
              break
            elif flag_l == True:
              lang_pitf_i.append(attr.replace('hasImportanceLevel: ', ''))
              break
        #suggestions to improve the ontolgy
        if sugg_flag in node:
            for attr in attrs:
                if 'hasDescription' in attr:
                    suggs.append(attr.replace('hasDescription: ', ''))
                    break
       

     if len(suggs) > 0 or len(m_pitf)> 0  > 0 :
        	s = " " 
		if len(suggs) > 0:
			s += "OOPS! has some suggestions to improve the ontology:\n"
			for i in range(len(suggs)):
				s += "%d. " % (i + 1) + suggs[i] +"\n"
		if len(m_pitf) > 0:
			s += "\n\nOOPS! has encountered some minor pitfalls:\n" 
			for i in range(len(m_pitf)):
				s += "%d. " % (i + 1) + m_pitf[i] +"\n"  
			if not 'Minor' in labels:
				labels.append("Minor")
                labels.append("enhancement")
                create_oops_issue_in_github(repo, ont_file, s, labels) 
                labels[:] = []
     if len(inf_pitf) > 0:
        i_p = p
        i_p += "inference. \n"
        i_p += "The Pitfalls are the following: \n"
        for i in range(len(inf_pitf)):
          i_p += "%d. " % (i + 1) + inf_pitf[i] + ". Importance level: "+ inf_pitf_i[i].replace('\"','') +"\n"
       # labels = ["Unit test bug", "Inference"]
          if not inf_pitf_i[i].replace('\"','') in labels:
          	labels.append(str(inf_pitf_i[i].replace('\"','')))
        labels.append("Unit test bug")
        labels.append("Inference")
        create_oops_issue_in_github(repo, ont_file, i_p, labels)
        labels[:] = []
     if len(mod_pitf) > 0:
        #p += "The Pitfalls are the following: \n"
        m_p = p
        m_p += "modeling. \n"
        m_p += "The Pitfalls are the following: \n"
        for i in range(len(mod_pitf)):
            m_p += "%d. " % (i + 1) + mod_pitf[i] + ". Importance level: "+ mod_pitf_i[i].replace('\"','') + "\n"
            if not mod_pitf_i[i].replace('\"','') in labels:
          	labels.append(str(mod_pitf_i[i].replace('\"','')))
        labels.append("Unit test bug")
        labels.append("Modeling")
        create_oops_issue_in_github(repo, ont_file, m_p, labels)
        labels[:] = []
     if len(met_pitf) > 0:
        met_p = p
        met_p += "metadata. \n"
        met_p += "The Pitfalls are the following: \n"
        for i in range(len(met_pitf)):
            met_p += "%d. " % (i + 1) + met_pitf[i] + ". Importance level: "+ met_pitf_i[i].replace('\"','') +"\n"
            if not met_pitf_i[i].replace('\"','') in labels:
          	labels.append(str(met_pitf_i[i].replace('\"','')))
        labels.append("Unit test bug")
        labels.append("Metadata")
        create_oops_issue_in_github(repo, ont_file, met_p, labels)
        labels[:] = []
     if len(lang_pitf) > 0:
        l_p  = p
        l_p += "ontology language. \n"
        l_p += "The Pitfalls are the following: \n"
        for i in range(len(lang_pitf)):
            l_p += "%d. " % (i + 1) + lang_pitf[i] + ". Importance level: "+ lang_pitf_i[i].replace('\"','') +"\n"
            if not lang_pitf_i[i].replace('\"','') in labels:
           	labels.append(str(lang_pitf_i[i].replace('\"','')))
        labels.append("Unit test bug")
        labels.append("Language")
        create_oops_issue_in_github(repo, ont_file, l_p, labels)
        labels[:] = []
         
             
    
##Functions to open and close old github issues    

def close_old_oops_issues_in_github(repo, ont_file):
    print 'will close old oops issues'
    for i in repo.get_issues(state='open'):
        if i.title == ('OOPS! Evaluation for ' + os.path.basename(ont_file)):
            i.edit(state='closed')
            
def close_old_acc_issues_in_github(repo):
    print 'will close old acceptance test issues'
    for i in repo.get_issues(state='open'):
    	print 'title'
	print i.title
	print 'body'
	print i.body
	print 'comment'
	print i.comment
	print 'all'
	print i
	
        if i.title == ('Acceptance test notification'):
            i.edit(state='closed')
            
def create_oops_issue_in_github(repo, ont_file, oops_issues,label):
    print 'will create an oops issue'
    try:
        repo.create_issue(
            'OOPS! Evaluation for ' + os.path.basename(ont_file), oops_issues, labels = label)
    except Exception as e:
        print 'exception when creating issue: ' + str(e)
        
# #########################################################################
# ###################################   main  #############################
# #########################################################################


if __name__ == "__main__":
    main()



          
          
 
