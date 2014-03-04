#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import tempfile
from os import environ

from PyQt4 import QtGui
from PyQt4 import QtCore

rc_file_name = environ.get('HOME') + '/.config/apt-notifierrc'
message_status = "not displayed"

# Check for updates, using subprocess.Popen
def check_updates():
    global message_status
    #Create an inline script (what used to be /usr/bin/apt-notifier-check-Updates) and then run it to get the number of updates.
    script = '''#!/bin/sh
    sorted_list_of_upgrades() 
    {
        #Create a sorted list of the names of the packages that are upgradeable.
        LC_ALL=en_US apt-get -o 'Debug::NoLocking=true' --trivial-only -V upgrade 2>/dev/null \
        |  sed -n '/upgraded:/,$p' | grep ^'  ' | awk '{ print $1 }' | sort
    }
    if [ -s /var/lib/synaptic/preferences ]; 
        then 
            #/var/lib/synaptic/preferences is a non-zero size file, which means there are packages pinned in Synaptic. 
            #Remove from the sorted_list_of_upgrades, packages that are pinned in Synaptic, and then get a count of remaining.
            
            sorted_list_of_upgrades | grep -vx $(grep 'Package:' /var/lib/synaptic/preferences | awk {'print "-e " $2'}) | wc -l
        
        else 
            #/var/lib/synaptic/preferences is either a zero byte file, meaning packages were pinned in Synaptic at some time in 
            # the past but none are currently pinned. Or the file is not present, meaning packages have never been pinned using 
            # Synaptic. In either case, just get a count of how many upgradeable packages are in the list.
            
            sorted_list_of_upgrades | wc -l
    fi
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["echo -n `sh %s` new updates available" % script_file.name],shell=True, stdout=subprocess.PIPE)
    # Read the output into a text string
    text = run.stdout.read(128)
    # Alter both Icon and Tooltip, depending on updates available or not 
    if text.startswith( "0" ):
        message_status = "not displayed"  # Resets flag once there are no more updates
        add_hide_action()
        if icon_config != "show":
            AptIcon.hide()
        else:
            AptIcon.setIcon(NoUpdatesIcon)
            AptIcon.setToolTip(text)
    else:
        AptIcon.setIcon(NewUpdatesIcon)
        AptIcon.show()
        AptIcon.setToolTip(text)
        add_upgrade_action()
        # Shows the pop up message only if not displayed before 
        if message_status == "not displayed":
            def show_message():
                AptIcon.showMessage("Updates", "You have " + text)
            Timer.singleShot(1000, show_message)
            message_status = "displayed"
   
# Define the command to run when clicking Tray Icon
def start_synaptic():
    run = subprocess.Popen(['/usr/bin/su-to-root -X -c synaptic'],shell=True).wait()
    check_updates()

def upgrade():
    script = '''#!/bin/bash
    [ ! -e /usr/bin/kdesu ] || kdesu -c "konsole -e apt-get upgrade"
    [ -e /usr/bin/kdesu ]   || su-to-root -X -c "x-terminal-emulator -e apt-get upgrade"
    sleep 5
    PID=`pidof apt-get | cut -f 1 -d " "`
    if [ $PID ]; then
        while (ps -p $PID > /dev/null); do
            sleep 5
        done
    fi
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(['sh %s' % script_file.name],shell=True).wait()
    check_updates()

# Define the action on clicking Tray Icon
def start_synaptic_activated(reason):
    if reason == QtGui.QSystemTrayIcon.Trigger:
        start_synaptic()

def read_icon_config():
    """Reads ~/.config/apt-notifierrc, returns 'show' if file doesn't exist or does not contain DontShowIcon"""
    command_string = "cat " + rc_file_name + " | grep -q DontShowIcon"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state != 0:
        return "show"

def set_noicon():
    """Reads ~/.config/apt-notifierrc. If "DontShowIcon blah blah blah" is already there, don't write it again"""
    command_string = "cat " + rc_file_name + " | grep -q DontShowIcon"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state != 0:
        file = open(rc_file_name, 'a')
        file.write ('[DontShowIcon] #Remove this entry if you want the apt-notify icon to show even when there are no upgrades available\n')
        file.close()
    AptIcon.hide()
    icon_config = "donot show"

def add_upgrade_action():
    ActionsMenu.clear()
    upgrade_action = ActionsMenu.addAction("Upgrade all packages")
    AptNotify.connect(upgrade_action, QtCore.SIGNAL("triggered()"), upgrade)
    add_help_action()
    add_quit_action()
    

def add_hide_action():
    ActionsMenu.clear()
    if icon_config == "show":
        hide_action = ActionsMenu.addAction("Hide until updates available")
        AptNotify.connect(hide_action,QtCore.SIGNAL("triggered()"),set_noicon)
    add_help_action()
    add_quit_action()
    

def add_quit_action():
    ActionsMenu.addSeparator()
    quit_action = ActionsMenu.addAction(QuitIcon,"Quit Apt-Notifier")
    AptNotify.connect(quit_action, QtCore.SIGNAL("triggered()"), AptNotify.exit)
    
def add_help_action():
    ActionsMenu.addSeparator()
    help_action = ActionsMenu.addAction(HelpIcon,"Apt-Notifier Help")
    help_action.triggered.connect(open_help)
    
def open_help():
    subprocess.Popen(['xdg-open file:///usr/share/synaptic/html/index.html'],shell=True)
    
# General application code	
def main():
    # Define Core objects, Tray icon and QTimer 
    global AptNotify
    global AptIcon
    global QuitIcon
    global icon_config
    global upgrade_action
    global quit_action    
    global Timer
    AptNotify = QtGui.QApplication(sys.argv)
    AptIcon = QtGui.QSystemTrayIcon()
    Timer = QtCore.QTimer()
    icon_config = read_icon_config()
    # Define the icons:
    global NoUpdatesIcon
    global NewUpdatesIcon
    global HelpIcon
    NoUpdatesIcon = QtGui.QIcon("/usr/share/icons/mnotify-none.png")
    NewUpdatesIcon  = QtGui.QIcon("/usr/share/icons/mnotify-some.png")
    HelpIcon = QtGui.QIcon("/usr/share/icons/Tango/22x22/apps/gnome-help.png")
    QuitIcon = QtGui.QIcon("/usr/share/icons/oxygen/22x22/actions/system-shutdown.png")
    # Create the right-click menu and add the Tooltip text
    global ActionsMenu
    ActionsMenu = QtGui.QMenu()
    AptIcon.connect( AptIcon, QtCore.SIGNAL( "activated(QSystemTrayIcon::ActivationReason)" ), start_synaptic_activated)
    AptNotify.connect(Timer, QtCore.SIGNAL("timeout()"), check_updates)
    # Integrate it together,apply checking of updated packages and set timer to every 5 minutes (1 second = 1000)
    check_updates()
    AptIcon.setContextMenu(ActionsMenu)
    if icon_config == "show":
        AptIcon.show()
    Timer.start(300000)
    if AptNotify.isSessionRestored():
        sys.exit(1)
    sys.exit(AptNotify.exec_())

if __name__ == '__main__':
    main()
