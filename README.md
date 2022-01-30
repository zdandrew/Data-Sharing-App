# pda-ota

## Over-the-air file sharing for Privacy Preserving Distributed Algorithms by the PennCil Lab at UPenn

PDA-OTA python file directory and documentation:

run.py – this is our main function.  It is deliberately very small and short, making it very easy for us to make specific changes to the run functionality of the code.  In this case, we must remember to remove the DEBUG statement from this file when it is time to put this into full production – we do not want a debug setting active on production servers!

pdaota – this folder contains all pda-ota files.  Python disallows hyphens in file names so I renamed it pdaoda; we could also just name it pda internally, or perhaps something else.

__init__.py – the initialization file.  Here is where all initialization will go, including setting up of the app itself, setting up mongoDB, setting up SMTP for eventual email functionality, etc.  If HTTPS requires setup procedures, those procedures will happen here.

routes.py – the main file for most of the basic functionality of the site.  Any pages that aren’t directly related to authentication, security, or forms will go here.

auth.py – authentication-related files will go here.  This includes all code related to logging in, logging out, checking user credentials i.e. username/password, etc.  This also includes any code we may later add for keeping you logged in, or sending emails for lost passwords, etc.

forms.py – all forms, including login/logout, creating new projects, etc will go here.  They are kept deliberately separate because we will likely take advantage of pyforms to make our lives easier and that package likes its code in a separate python file.

crypto.py – all cryptography and/or security related stuff goes here.  If we decide to implement RSA or anything like that, it will go here – otherwise, if we go with HTTPS and decide to implement a solution with our own certificate, the code for handling that will happen here.

lib.py – the library file.  This python file will contain all miscellaneous helper functions that are not directly related to the website.  Stuff like, helper functions for splitting DOM objects, or functions that might have use across the entire site (such as the wrapper to see if a user is logged in) will be placed here.
