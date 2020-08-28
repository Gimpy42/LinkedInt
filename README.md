# Credits

Original Scraper by Danny Chrastil (@DisK0nn3cT): https://github.com/DisK0nn3cT/linkedin-gatherer
Original tool by Vincent Yiu (@vysec, @vysecurity): https://github.com/vysecurity/LinkedInt.git

# Installation
```
pip install -r requirements.txt
```

# Change Log

[v0.1 BETA 28-08-2020]
Additions:
* Properly removed special caracter from email
* Removing title from lastname to properly generate email
* Multiple Company ID supporter with ID choice if required
* Fetching occupation start date from profile

# To-Do List

* Add Natural Language Processing techniques on titles to discover groups of similar titles to be stuck into same "department". A department column could be added to the csv and html.

# Usage

Put in LinkedIn credentials in LinkedInt.cfg
Put Hunter.io API key in LinkedInt.cfg
Run LinkedInt.py and follow instructions

# Example

```
██╗     ██╗███╗   ██╗██╗  ██╗███████╗██████╗ ██╗███╗   ██╗████████╗
██║     ██║████╗  ██║██║ ██╔╝██╔════╝██╔══██╗██║████╗  ██║╚══██╔══╝
██║     ██║██╔██╗ ██║█████╔╝ █████╗  ██║  ██║██║██╔██╗ ██║   ██║
██║     ██║██║╚██╗██║██╔═██╗ ██╔══╝  ██║  ██║██║██║╚██╗██║   ██║
███████╗██║██║ ╚████║██║  ██╗███████╗██████╔╝██║██║ ╚████║   ██║
╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═══╝   ╚═╝

Providing you with Linkedin Intelligence
Author: Gimpy 
Original version by Vincent Yiu (@vysec, @vysecurity)
[*] Enter search Keywords (use quotes for more percise results)
"General Motors"

[*] Enter filename for output (exclude file extension)
generalmotors

[*] Filter by Company? (Y/N):
Y

[*] Specify a Company ID (Provide ID or leave blank to automate):


[*] Enter e-mail domain suffix (eg. contoso.com):
gm.com

[*] Select a prefix for e-mail generation (auto,full,firstlast,firstmlast,flast,first.last,fmlast):
auto

[*] Automaticly using Hunter IO to determine best Prefix
[!] {first}.{last}
[+] Found first.last prefix
```
