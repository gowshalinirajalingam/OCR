
import sys
import logging
from logging import critical, error, info, warning, debug
import json
import pandas as pd
from fuzzywuzzy import fuzz
import numpy as np

logging.basicConfig(filename="std.log", 
					format='%(asctime)s %(message)s', 
					filemode='w') 

#Let us Create an object 
logger=logging.getLogger() 

#Now we are going to Set the threshold of logger to DEBUG 
logger.setLevel(logging.DEBUG) 

logger.info("OCR TESTING")


def Compare_key_value(aList_expect, alist_test, expect_page_no):
    
    logger.info("PAGE NUMBER"+str(expect_page_no)+ " KEY VALUE VALIDATION...")
    logger.info("=============================================================")
    
    missing_keys = []
    not_matched_keys = []
    key_val_dict = {}
    
    Key_Values_expect = aList_expect['Key_Values']
    count_expect = len(Key_Values_expect)
    #logger.info('Expected keys count '+str(count_expect))
    
    Key_Values_test = alist_test['Key_Values']
    count_test = len(Key_Values_test)
    #logger.info('Actual keys count '+str(count_test))
    
    
    if count_expect == count_test:
        logger.info("KEYS COUNT MATCHED...")
    else:
        acc = round(count_test*100/count_expect,2)
        logger.info("KEYS COUNT NOT MATCHED... | MATCHED % : "+str(acc))
#    Key_Values_expect  ={'Bill_Ref_Number': 'Flexi MSV Deducted', 'Tax_Invoice_Date': 'R', 'Visit_Date': ':28.09.2018 0950 hrs', 'Payment_Class': ': Cash/Credit', 'GST_REG_NO': ' : M2-0088821-9', 'Page': ' 1 of 1', 'Total_Charges_Payable': '32.00'}
#    Key_Values_test  ={ 'Tax_Invoice_Date': 'r', 'Visit_Date': ':28.09.2018 0950 hrs', 'Payment_Class': ': Cash/Credit', 'GST_REG_NO': ' : M2-0088821-9', 'Page': ' 1 of 1', 'Total_Charges_Payable': '32.00'}

    for e in list(Key_Values_expect.keys()):
        if e in Key_Values_test.keys():
        
            #compare keys
            try:
                acc = fuzz.ratio(str(Key_Values_expect[e]), str(Key_Values_test[e]))
                key_val_dict[e] = [acc]
                
                if acc == 0:
                    not_matched_keys.append(e)
                    
                
            except Exception as e:
                error(str(e))
        else:
            logger.info("KEY "+e+" IS MISSING")
            missing_keys.append(e)
            
    if len(missing_keys) > 0 or len(not_matched_keys) :
        logger.info("THE KEY VALUE VALIDATION STATUS IS FAILUE...")
    else:
        logger.info("THE KEY VALUE VALIDATION STATUS IS SUCCESS...")
            
    key_val_df = pd.DataFrame.from_dict(key_val_dict)
    key_val_df.index = pd.Index(['sim_score%'],name='Key')   #Give header to name and rows inside array.header will become index of df
    key_val_df = key_val_df.T
    key_val_df = key_val_df.reset_index()
    key_val_df.rename(columns = {'index':'Key'}, inplace = True)


    #Calculate nad Append avg score in the dataframe
    avg_sim_score = key_val_df['sim_score%'].sum(axis=0)/key_val_df.shape[0]
    avg_sim_score = round(avg_sim_score,2)
    
    avg_acc_df = pd.DataFrame({"Key":["AVG SIM SCORE"],"sim_score%":[avg_sim_score]}) 
    key_val_df = pd.concat([key_val_df, avg_acc_df])
    
    logger.info("AVG SIM SCORE FOR KEY VALUE EXTRACTION:"+ str(avg_sim_score))


    #write dataframe to excel for the 1st time like this
    key_val_df.to_excel("/home/senzmatepc27/Desktop/senzmate/senzmate_git/OCR/Result_"+str(expect_page_no)+".xlsx", sheet_name='Key Value Extraction')

    
    logger.info("MATCHING SCORE OF EXISTING KEYS...")
    logger.info(key_val_df)

    logger.info("\n")

    return key_val_dict, missing_keys, not_matched_keys
            
          
        
        
        
def Compare_Table_values(aList_expect, alist_test, expect_page_no):
    
    logger.info("PAGE NUMBER"+str(expect_page_no)+ " TABLE VALIDATION...")
    logger.info("=============================================================")

    acc_table = pd.DataFrame()
    acc_dict = {}
    cols_expect = []
    cols_test = []
    missed_rows_index = []
    missed_columns = []
    
    acc_list = []
    
    table_expect = aList_expect['Table']
    rows_expect = len(table_expect)
    logger.info('Expected row count '+str(rows_expect))
    
    table_test = alist_test['Table']
    rows_test = len(table_test)
    logger.info('Actual row count '+str(rows_test))
    
    
    for i in range(rows_expect):
        
        try:
            cols_expect.extend(list(table_expect[i].keys()))  #extend means only append the values from list
            cols_test.extend(list(table_test[i].keys()))

            cols_expect = set(cols_expect)  # dict
            cols_test = set(cols_test)    # dict

            cols_expect = list(cols_expect)  #list
            cols_test = list(cols_test)     #list

    
            for c in cols_expect:
                if c in cols_test:
                    acc = fuzz.ratio(str(table_expect[i][c]), str(table_test[i][c]))
                    acc_dict[c] = acc
                else:
                     logger.info('Missed column: '+c)
                     missed_columns.append(c)
                     acc_dict[c] = None
                     
#            acc_dict = {k:[v] for k,v in acc_dict.items()}  # WORKAROUND
#            acc_table = acc_table.append(pd.DataFrame(acc_dict, index=[i]) )       
            acc_list.insert(i, acc_dict) 

            acc_dict = {}
        except IndexError:
            missed_rows_index.append(i)  #rows in expected json but not in test json
    
    acc_table = pd.concat([acc_table, pd.DataFrame(acc_list)], axis=0, ignore_index=True)

    #get unique values. bcz when exception comes line after 99 won't run. so cols_expect will be having many duplicates.
    cols_expect = set(cols_expect)  # dict
    cols_expect = list(cols_expect)  #list
    
    missed_columns = set(missed_columns)  # dict
    missed_columns = list(missed_columns)  #list
    

    #Calculate nad Append avg score in the dataframe
    acc_table['SUM'] = acc_table[cols_expect].sum(axis=1) 
    acc_table['AVG'] = round(acc_table['SUM']/(len(cols_expect)-len(missed_columns)))  #Don't devide by cols_expect. because we should ignore missed columns
    avg_acc = acc_table['AVG'].sum(axis=0)/rows_expect
    avg_acc = round(avg_acc,2)
    
    avg_acc_df = pd.DataFrame({"SUM":"AVG SIM SCORE","AVG":[avg_acc]}) 
    acc_table = pd.concat([acc_table, avg_acc_df], ignore_index = True)
    acc_table = acc_table.astype(str)
    
    #write dataframe to excel for the 2nd< time like this
    with pd.ExcelWriter("/home/senzmatepc27/Desktop/senzmate/senzmate_git/OCR/Result_"+str(expect_page_no)+".xlsx",mode='a') as writer:
        acc_table.to_excel(writer, sheet_name='Table Extraction')
    
    logger.info('MATCHING SCORE OF EACH CELL FOR THE TABLE')    
    logger.info(acc_table)       
    
    logger.info('AVG MATCHING SCORE OF THE TABLE : '+str(avg_acc))  
    
    if avg_acc != 100.0:
        logger.info("THE TABLE VALIDATION STATUS IS FAILUE WITH AVG ACCURACY: "+str(avg_acc))
    else:
        logger.info("THE TABLE VALIDATION STATUS IS SUCCESS...")
        
    logger.info("\n")

    return   acc_table     
            
def Compare_raw_values(aList_expect, alist_test, expect_page_no):
    
    logger.info("PAGE NUMBER"+str(expect_page_no)+ " RAW DATA VALIDATION...")
    logger.info("=============================================================")
    
#    aList_expect = aList_expect[0]
#    alist_test = alist_test[0]
    
    raw_expect = aList_expect['raw_extraction'][0]  
    raw_test = alist_test['raw_extraction'][0]
    
    sim_score_dict = {}
    raw_test_keys = list(raw_test.keys())
    
    for re in raw_expect:
        if re in raw_test_keys:
            acc = fuzz.ratio(str(raw_expect[re]), str(raw_test[re])  ) 
            sim_score_dict[re] = [raw_expect[re],str(raw_test[re]) , acc]
        
        
        
    #Calculate nad Append avg score in the dataframe
    sim_score_df = pd.DataFrame.from_dict(sim_score_dict) 
    sim_score_df.index = pd.Index(['raw_expect','raw_extracted','sim_score%'],name='ID')
    sim_score_df = sim_score_df.T
    sim_score_df = sim_score_df.reset_index()
    sim_score_df.rename(columns = {'index':'ID'}, inplace = True)
    
    avg_sim_score = sim_score_df['sim_score%'].sum(axis=0)/sim_score_df.shape[0]
    avg_sim_score = round(avg_sim_score,2)
    
    avg_sim_score_df = pd.DataFrame({
                    "raw_extracted":["AVG SIM SCORE"], 
                    "sim_score%":[avg_sim_score]})
    
    sim_score_df = pd.concat([sim_score_df, avg_sim_score_df], ignore_index = True)
    sim_score_df = sim_score_df.astype(str)

    #write dataframe to excel for the 2nd< time like this
    with pd.ExcelWriter("/home/senzmatepc27/Desktop/senzmate/senzmate_git/OCR/Result_"+str(expect_page_no)+".xlsx",mode='a') as writer:
        sim_score_df.to_excel(writer, sheet_name='Raw Extraction')
        
    logger.info(sim_score_df)
        

    

def read_expected_json(file_path):
    f = open(file_path)
    aList_expect = json.load(f)
    
    return aList_expect
    
def read_testing_json(file_path):
    f = open(file_path)
    alist_test = json.load(f)
    
    return alist_test
        
        
if __name__ == '__main__':
    
    try:
        
        #READ EXPECTED JSON
        file_path_expect = '/home/senzmatepc27/Desktop/senzmate/senzmate_git/OCR/samples Medical Receipts_sample_002_new_expected.json'
#        file_path_expect = '/home/senzmatepc27/Desktop/senzmate/senzmate_git/OCR/test_new_expected.json'
        aList_expect = read_expected_json(file_path_expect)

        #READ TEST FILE
        file_path = '/home/senzmatepc27/Desktop/senzmate/senzmate_git/OCR/samples Medical Receipts_sample_002_new.json'
#        file_path = '/home/senzmatepc27/Desktop/senzmate/senzmate_git/OCR/test_new.json'
        alist_test = read_testing_json(file_path)

        # number of tables in the file
        num_tbls=len(aList_expect)

        for id in range(num_tbls):
            
            expect_page_no = aList_expect[id]['Page_Number']
            print("expect_page_no",expect_page_no)


            for at in alist_test:
               print("at['Page_Number']",at['Page_Number'])

               if  at['Page_Number'] == expect_page_no:
                   Compare_key_value(aList_expect[id], at, expect_page_no)
            
                   Compare_Table_values(aList_expect[id], at, expect_page_no)

                   Compare_raw_values(aList_expect[id], at, expect_page_no)
    except Exception as e:
        error(str(e))
