# catalog
This is my fourth project in Udacity's [Full Stack Web Development Nanodegree] (https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).

## Files
### - application.py 
The main python file controling the back-end functionality of the this catalog webpage.

### - static folder
The stylesheet used to style the blog.

### - templates folder
Contains all of the HTML files linked to in the blog.

### - add_categories.py
Contains the code used to create the categories on the website. This functionality is not available to users, so I created them using a separate file.

### - database_setup.py
Python file setting up the tables and relationships in my database, as well as a definition for creating JSON APIs.

## Requirements
For Mac:
This project requires that you have python dowloaded on your computer. I used Vagrant and [VirtualBox] (https://www.virtualbox.org) to run my program. Once you have your environment set up, create the database using the command: 

<code> python database_setup.py </code> 

Next, create the catalog categories with the command: 

<code> python add_categories.py </code> 

Finally, run the command: 

<code> python application.py </code> 

and view the project at [http://localhost:5000/](http://localhost:5000)
