# L-G_Scheduler
Hopefully we can use this!!!

I will try to make this as easy as possible for you. However, for simplicity in explanation, it is best to do this on a MacOS or Linux computer -- these commands will not always work on Windows. 
Note: do not include the quotations in the terminal commands.
1. Open temrinal
2. Navigate to the directory of where the GitHub repository is. Preferabily, save it to desktop and follow these commadns.
   - cd desktop
   - cd "___Whatever the name of the downloaded folder is__" (obviously not this but what the name is)
3. in terminal enter this to make files executable: "chmod +x run.sh"
4. in terminal enter this to run everything: "./run.sh"
5.   









.
.
.
.
DO THIS IS THE run.sh DOCUMENT IS NOT WORKING....

1. Download all of of these files. This will result in a zip file on your computer. Click on the zip to make into into its own folder
2. Set up a virtual enviroment onto your device
   - Download any 3.x python versions at https://www.python.org/downloads/
   - Navigate to the current directory of the scheduling software files. For ease,  I recommend putting the file on the desktop or downloads area of your storage. Go to the terminal and type: "cd desktop" or: "cd downloads" depending on where you place the folder respectively-- cd mean change directory so you are move to that folder manually. Then input the command: "python -m venv venv". This will make a folder within your software folder containing the virtual environment.
   - Activate the virtual environment by inputting the command into the terminal. "venv\Scripts\activate" (on Windows) and "source venv/bin/activate" (on MacOS / Linux). 
3. With the virtual machine activated, we need to install the required packages. Execute this command which will call the requirements.txt file and execute all the necessary library downloads. Don't worry about this taking up too much storage (at most 1 Gb).
    - Call in terminal: "lib_requirements.txt"
4. Once completely done, it is best practice to call the command "deactivate" in your terminal... but I never do it.

As a quicker rundown of steps:
1. Download this GitHub repository
3. Download python 3 or later
4. Move downloaded GitHub downloaded repository to your desktop
5. Open the terminal
6. Write in terminal: "cd desktop"
7. Write in terminal: "python -m venv venv"
8. Write in terminal (on Mac): "source venv/bin/activate"
9. Write in terminal: "lib_requirements.txt"
10. Once all done, call "deactivate" in terminal
