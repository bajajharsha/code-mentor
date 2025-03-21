REWRITE_USER_PROMPT_TEMPLATE = """
I will give you an orignal code of a file and then a rewritten code of the same file 
you have to figure out where in the orignal code the rewritten code will go 
make sure that the rewritten code is correct and working
here is the orignal file : {orignal_code}
here is the improved functionality that needs to be added to orignal file: {rewritten_code}
write a merged code that will have both the orignal code and the rewritten code in the correct order
enclose the code in a code tag <code> </code>
"""

REWRITE_QUERY_TEMPLATE = """ for given prompt answer me the merged code that will have both the orignal code and the rewritten code in the correct order"""