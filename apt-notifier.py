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
    global text
    #Create an inline script (what used to be /usr/bin/apt-notifier-check-Updates) and then run it to get the number of updates.
    script = '''#!/bin/sh
    sorted_list_of_upgrades() 
    {
        #Create a sorted list of the names of the packages that are upgradeable.
        LC_ALL=en_US apt-get -o 'Debug::NoLocking=true' --trivial-only -V $(grep ^UpgradeType ~/.config/apt-notifierrc | cut -f2 -d=) 2>/dev/null \
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
    # run = subprocess.Popen(["echo -n 'using upgrade method: '\\\x60apt-get' '$(grep ^UpgradeType ~/.config/apt-notifierrc | cut -f2 -d=)\\\x60"],shell=True, stdout=subprocess.PIPE)
    # Read the output into a text string
    # text2 = run.stdout.read(128)

    # Alter both Icon and Tooltip, depending on updates available or not 
    if text.startswith( "0" ):
        message_status = "not displayed"  # Resets flag once there are no more updates
        add_hide_action()
        if icon_config != "show":
            AptIcon.hide()
        else:
            AptIcon.setIcon(NoUpdatesIcon)
            AptIcon.setToolTip("0 updates available")
            #AptIcon.setToolTip("0 updates available\n"+text2)
    else:
        if text.startswith( "1 " ):
            AptIcon.setIcon(NewUpdatesIcon)
            AptIcon.show()
            AptIcon.setToolTip("1 new update available")
            #AptIcon.setToolTip("1 new update available\n"+text2)
            add_rightclick_actions()
            # Shows the pop up message only if not displayed before 
            if message_status == "not displayed":
                def show_message():
                    AptIcon.showMessage("Updates", "You have 1 new update available")
                Timer.singleShot(1000, show_message)
                message_status = "displayed"
        else:
            AptIcon.setIcon(NewUpdatesIcon)
            AptIcon.show()
            AptIcon.setToolTip(text)
            #AptIcon.setToolTip(text+"\n"+text2)
            add_rightclick_actions()
            # Shows the pop up message only if not displayed before 
            if message_status == "not displayed":
                def show_message():
                    AptIcon.showMessage("Updates", "You have " + text)
                Timer.singleShot(1000, show_message)
                message_status = "displayed"
   
def start_synaptic():
    run = subprocess.Popen(['/usr/bin/su-to-root -X -c synaptic'],shell=True).wait()
    check_updates()

def viewandupgrade():
    initialize_aptnotifier_prefs()
    script = '''#!/bin/bash
    DoUpgrade(){
      case $1 in
        0)
        BP="1"
        if (xprop -root | grep -q -i kde)
          then
            # running KDE
            # can't get su-to-root to work in newer KDE's, so use kdesu for authentication  
            # if x-terminal-emulator is set to xfce4-terminal.wrapper, use xfce4-terminal instead 
            #   because the --hold option doesn't work with the wrapper. Also need to enclose the
            #   apt-get command in single quotes.
            # if x-terminal-emulator is set to xterm, use konsole instead, if it's available (it should be)
            case $(readlink -e /usr/bin/x-terminal-emulator | xargs basename) in
              konsole               )                                             kdesu -c        "konsole -e  bash $TMP/upgradeScript " ;;
              xfce4-terminal.wrapper)                                             kdesu -c "xfce4-terminal -e 'bash $TMP/upgradeScript'" ;;
              xterm                 ) [ ! -e /usr/bin/konsole ]        ||         kdesu -c        "konsole -e  bash $TMP/upgradeScript "
                                      [   -e /usr/bin/konsole ]        ||         kdesu -c          "xterm -e  bash $TMP/upgradeScript " ;;
              *                     )                                                                                                    ;;
            esac  
          else
            # running a non KDE desktop
            # use su-to-root for authentication, it should end up using gksu
            # if x-terminal-emulator is set to xfce4-terminal.wrapper, use xfce4-terminal instead 
            #   because the --hold option doesn't work with the wrapper. Also need to enclose the
            #   apt-get command in single quotes.
            # if x-terminal-emulator is set to xterm, use xfce4-terminal instead, if it's available (it is in MX) 
            case $(readlink -e /usr/bin/x-terminal-emulator | xargs basename) in
              konsole               )                                     su-to-root -X -c        "konsole -e  bash $TMP/upgradeScript " ;;
              xfce4-terminal.wrapper)                                     su-to-root -X -c "xfce4-terminal -e 'bash $TMP/upgradeScript'" ;;
              xterm                 ) [ ! -e /usr/bin/xfce4-terminal ] || su-to-root -X -c "xfce4-terminal -e 'bash $TMP/upgradeScript'"
                                      [   -e /usr/bin/xfce4-terminal ] || su-to-root -X -c          "xterm -e  bash $TMP/upgradeScript " ;;             
              *                     )                                                                                                    ;;
            esac
        fi
        ;;
        
        2)
        BP="1"
        ;;
        
        4)
        BP="0"
        sed -i 's/UpgradeType='$UpgradeType'/UpgradeType='$OtherUpgradeType'/' ~/.config/apt-notifierrc
        ;;
        
        *)
        BP="1"
        ;;
        
       esac 
    }

    BP="0"
    while [ $BP != "1" ]
      do

        UpgradeType=$(grep ^UpgradeType ~/.config/apt-notifierrc | cut -f2 -d=)
        if [ "$UpgradeType" = "upgrade"      ]; then
          OtherUpgradeType="dist-upgrade"
        fi
        if [ "$UpgradeType" = "dist-upgrade" ]; then
          OtherUpgradeType="upgrade"
        fi
  
        UpgradeAssumeYes=$(grep ^UpgradeAssumeYes ~/.config/apt-notifierrc | cut -f2 -d=)
        UpgradeAutoClose=$(grep ^UpgradeAutoClose ~/.config/apt-notifierrc | cut -f2 -d=)
      
        TMP=$(mktemp -d /tmp/apt-notifier.XXXXXX)
        echo "apt-get $UpgradeType" > "$TMP"/upgrades
        apt-get -o Debug::NoLocking=true --trivial-only -V $UpgradeType 2>/dev/null >> "$TMP"/upgrades
        
        #remove Synaptic pinned packages from "$TMP"/upgrades, so they don't get displayed in the 'View and Upgrade' window -- original method
        #for i in $(grep ^Package: /var/lib/synaptic/preferences 2>/dev/null | awk '{print $2}' 2>/dev/null); do sed -i '/'$i' (.*=>.*)/d' "$TMP"/upgrades 2>/dev/null; done
        
        #remove Synaptic pinned packages from "$TMP"/upgrades, so they don't get displayed in the 'View and Upgrade' window -- new method
        for i in $(grep -A1 Package: /var/lib/synaptic/preferences | sed 's/Package: //; s/Pin: version /@/; /--/d' | awk 'ORS=" "' | sed 's/ @/_/g');\
          do \
            j="$(echo $i | sed 's/_/ /' | awk '{print $1" ("$2" =>"}')";\
            sed -i '/'"$j"'/d' "$TMP"/upgrades 2>/dev/null;\
          done

        #correct upgrades count -- original method
        #PossiblyWrongNumberOfUpgrades=$(grep ^[0-9]*' upgraded,' -o "$TMP"/upgrades | awk '{print $1}')
        #CorrectedNumberOfUpgrades=$(sed -n '/upgraded:$/,$p' "$TMP"/upgrades | grep ^'  ' | wc -l)
        #sed -i 's/^'$PossiblyWrongNumberOfUpgrades' upgraded, /'$CorrectedNumberOfUpgrades' upgraded, /' "$TMP"/upgrades
        
        #correct upgrades count -- revision 1
        #PossiblyWrongNumberOfUpgrades=$(tac "$TMP"/upgrades|sed '1,2d'|head -n1|awk '{print $1,$2,$3}'|grep -o -e^[1-9][0-9]* -e.[1-9][0-9]*|sed 's/^[[:space:]]//')
        #CorrectedNumberOfUpgrades=$(sed -n '/upgraded:$/,$p' "$TMP"/upgrades | grep ^'  ' | wc -l)
        #sed -i 's/^'$PossiblyWrongNumberOfUpgrades' upgraded, /'$CorrectedNumberOfUpgrades' upgraded, /' "$TMP"/upgrades        

        #correct upgrades count -- revision 2 (attempts to do a better job of correcting the upgrades count for non-english users)
        #CorrectedNumberOfUpgrades=$(grep '=>' $TMP/upgrades | wc -l)
        CorrectedNumberOfUpgrades=$(tac "$TMP"/upgrades | grep -e:$ -e：$ -m1 -B99999 | grep '=>'| wc -l) 
        tac "$TMP"/upgrades | sed '3s/[1-9][0-9]*/'$CorrectedNumberOfUpgrades'/' | tac >> "$TMP"/upgrades
        sed -i "1,$(echo -n $(echo $(cat "$TMP"/upgrades | wc -l)/2 | bc))d" "$TMP"/upgrades

        yad \
        --window-icon=/usr/share/icons/mnotify-some.png \
        --width=640 \
        --height=480 \
        --center \
        --title "apt-notifier View and Upgrade, previewing: apt-get "$UpgradeType \
        --form \
          --field :TXT "$(cat "$TMP"/upgrades)" \
          --field="use apt-get's --yes option for $UpgradeType":CHK $UpgradeAssumeYes \
          --field="automatically close terminal window when apt-get $UpgradeType complete":CHK $UpgradeAutoClose \
        --button "switch to 'apt-get "$OtherUpgradeType"'":4 \
        --button gtk-ok!!apt-get\ $UpgradeType:0 \
        --button gtk-cancel:2 \
        --buttons-layout=spread \
        2>/dev/null \
        > "$TMP"/results 

        echo $?>>"$TMP"/results

        # if the View and Upgrade yad window was closed by one of it's 3 buttons, 
        # then update the UpgradeAssumeYes & UpgradeAutoClose flags in the 
        # ~/.config/apt-notifierrc file to match the checkboxes
        if [ $(tail -n1 "$TMP"/results) -eq 0 ]||\
           [ $(tail -n1 "$TMP"/results) -eq 2 ]||\
           [ $(tail -n1 "$TMP"/results) -eq 4 ];
          then
            if [ "$(head -n1 "$TMP"/results | rev | awk -F \| '{ print $3}' | rev)" = "TRUE" ];
              then
                sed -i 's/UpgradeAssumeYes=false/UpgradeAssumeYes=true/' ~/.config/apt-notifierrc
              else
                sed -i 's/UpgradeAssumeYes=true/UpgradeAssumeYes=false/' ~/.config/apt-notifierrc
            fi
            if [ "$(head -n1 "$TMP"/results | rev | awk -F \| '{ print $2}' | rev)" = "TRUE" ];
              then
                sed -i 's/UpgradeAutoClose=false/UpgradeAutoClose=true/' ~/.config/apt-notifierrc
              else
                sed -i 's/UpgradeAutoClose=true/UpgradeAutoClose=false/' ~/.config/apt-notifierrc
            fi
          else
            :
        fi

        # refresh UpgradeAssumeYes & UpgradeAutoClose 
        UpgradeAssumeYes=$(grep ^UpgradeAssumeYes ~/.config/apt-notifierrc | cut -f2 -d=)
        UpgradeAutoClose=$(grep ^UpgradeAutoClose ~/.config/apt-notifierrc | cut -f2 -d=)

        # build a upgrade script to do the apt-get upgrade (or dist-upgrade)
        echo "#!/bin/bash"> "$TMP"/upgradeScript
        echo "echo 'apt-get '"$UpgradeType>> "$TMP"/upgradeScript
        echo 'SynapticPins=$(mktemp /etc/apt/preferences.d/synaptic-XXXXXX-pins)'>> "$TMP"/upgradeScript
        echo 'ln -sf /var/lib/synaptic/preferences "$SynapticPins" 2>/dev/null'>> "$TMP"/upgradeScript
        if [ "$UpgradeAssumeYes" = "true" ];
          then
            echo "apt-get -q --assume-yes "$UpgradeType>> "$TMP"/upgradeScript
          else
            echo "apt-get -q "$UpgradeType>> "$TMP"/upgradeScript
        fi 
        echo "echo">> "$TMP"/upgradeScript
        echo 'rm -f "$SynapticPins"'>> "$TMP"/upgradeScript
        if [ "$UpgradeAutoClose" = "true" ];
          then
            echo "echo 'apt-get '"$UpgradeType"' complete (or was canceled)'">> "$TMP"/upgradeScript
            echo "echo">> "$TMP"/upgradeScript
            echo "sleep 1">> "$TMP"/upgradeScript
            echo "exit 0">> "$TMP"/upgradeScript
          else
            echo "echo 'apt-get '"$UpgradeType"' complete (or was canceled)'">> "$TMP"/upgradeScript
            echo "echo">> "$TMP"/upgradeScript
            echo "echo -n 'this terminal window can now be closed '">> "$TMP"/upgradeScript
            echo "read -sn 1 -p '(press any key to close)' -t 999999999">> "$TMP"/upgradeScript
            echo "echo">> "$TMP"/upgradeScript
            echo "exit 0">> "$TMP"/upgradeScript
        fi

        DoUpgrade $(tail -n1 "$TMP"/results)
    
        rm -rf "$TMP"

      done

    sleep 2
    PID=`pidof apt-get | cut -f 1 -d " "`
    if [ $PID ]; then
        while (ps -p $PID > /dev/null); do
            sleep 2
        done
    fi
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(['sh %s' % script_file.name],shell=True).wait()
    check_updates()

def initialize_aptnotifier_prefs():

    """Create/initialize preferences in the ~/.config/apt-notifierrc file  """
    """if they don't already exist. Remove multiple entries and those that """
    """appear to be invalid.                                               """ 

    script = '''#! /bin/bash

    #test if ~/.config/apt-notifierrc contains a UpgradeType=* line and that it's a valid entry
    grep -q -e ^"UpgradeType=upgrade" -e^"UpgradeType=dist-upgrade" ~/.config/apt-notifierrc
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a UpgradeType=* line not present,
      #or not equal to "upgrade" or "dist-upgrade"
      #initially set it to "UpgradeType=upgrade"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*UpgradeType.*/Id' ~/.config/apt-notifierrc 
      echo "UpgradeType=upgrade">> ~/.config/apt-notifierrc
    fi

    #test if ~/.config/apt-notifierrc contains a UpgradeAssumeYes=* line and that it's a valid entry
    grep -q -e ^"UpgradeAssumeYes=true" -e^"UpgradeAssumeYes=false" ~/.config/apt-notifierrc
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a UpgradeAssumeYes=* line not present,
      #or not equal to "true" or "false"
      #initially set it to "UpgradeAssumeYes=false"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*UpgradeAssumeYes.*/Id' ~/.config/apt-notifierrc 
      echo "UpgradeAssumeYes=false">> ~/.config/apt-notifierrc
    fi

    #test if ~/.config/apt-notifierrc contains a UpgradeAutoClose=* line and that it's a valid entry
    grep -q -e ^"UpgradeAutoClose=true" -e^"UpgradeAutoClose=false" ~/.config/apt-notifierrc
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a UpgradeAutoClose=* line not present,
      #or not equal to "true" or "false"
      #intially set it to "UpgradeAutoClose=false"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*UpgradeAutoClose.*/Id' ~/.config/apt-notifierrc 
      echo "UpgradeAutoClose=false">> ~/.config/apt-notifierrc
    fi

    #test if ~/.config/apt-notifierrc contains a LeftClick=* line and that it's a valid entry
    grep -q -e ^"LeftClick=ViewAndUpgrade" -e^"LeftClick=Synaptic" ~/.config/apt-notifierrc
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a LeftClick line not present,
      #or not equal to "ViewAndUpgrade" or "Synaptic"
      #initially set it to "LeftClick=Synaptic"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*LeftClick.*/Id' ~/.config/apt-notifierrc 
      echo "LeftClick=Synaptic">> ~/.config/apt-notifierrc
    fi

    #cleanup any blank lines or lines with only whitespace
    sed -i '/^[[:space:]]*$/d' ~/.config/apt-notifierrc

    '''

    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(['sh %s' % script_file.name],shell=True).wait()

def aptnotifier_prefs():
    initialize_aptnotifier_prefs()
    script = '''#! /bin/bash
    TMP=$(mktemp -d /tmp/apt_notifier_preferences_dialog.XXXXXX)
    touch "$TMP"/output
    cat << EOF > "$TMP"/DIALOG
    <window title="MX Apt Notifier preferences" icon-name="mnotify-some">
      <vbox>
        <frame  upgrade behaviour   (also affects notification count)   >
          <radiobutton active="@UpgradeBehaviourAptGetUpgrade@">
            <label>apt-get upgrade</label>
            <variable>UpgradeType_upgrade</variable>
            <action>:</action>
          </radiobutton>
          <radiobutton active="@UpgradeBehaviourAptGetDistUpgrade@">
            <label>apt-get dist-upgrade</label>
            <variable>UpgradeType_dist-upgrade</variable>
            <action>:</action>
          </radiobutton>
        </frame>
        <frame  left-click behaviour   (when updates are available)   >
          <radiobutton active="@LeftClickBehaviourSynaptic@">
            <label>opens Synaptic </label>
            <variable>LeftClickSynaptic</variable>
            <action>:</action>
          </radiobutton>
          <radiobutton active="@LeftClickBehaviourViewAndUpgrade@">
            <label>opens MX Apt Notifier "View and Upgrade" window</label>
            <variable>LeftClickViewAndUpgrade</variable>
            <action>:</action>
          </radiobutton>
        </frame>
        <frame>
          <checkbox active="@UpgradeAssumeYes@">
            <label>use apt-get --yes option for upgrade/dist-upgrade</label>
            <variable>UpgradeAssumeYes</variable>
            <action>:</action>
          </checkbox>
        </frame>
        <frame>
          <checkbox active="@UpgradeAutoClose@">
            <label>automatically close terminal window when apt-get upgrade/dist-upgrade complete</label>
            <variable>UpgradeAutoClose</variable>
            <action>:</action>
          </checkbox>
        </frame>
      <hbox>
        <button ok> </button>
        <button cancel> </button>
      </hbox>
      </vbox>
    </window>
EOF

    # edit placeholders in "$TMP"/DIALOG to set initial settings of the radiobuttons & checkboxes 
    sed -i 's/@UpgradeBehaviourAptGetUpgrade@/'$(if [ $(grep UpgradeType=upgrade ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@UpgradeBehaviourAptGetDistUpgrade@/'$(if [ $(grep UpgradeType=dist-upgrade ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@LeftClickBehaviourSynaptic@/'$(if [ $(grep LeftClick=Synaptic ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@LeftClickBehaviourViewAndUpgrade@/'$(if [ $(grep LeftClick=ViewAndUpgrade ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@UpgradeAssumeYes@/'$(grep UpgradeAssumeYes ~/.config/apt-notifierrc | cut -f2 -d=)'/' "$TMP"/DIALOG
    sed -i 's/@UpgradeAutoClose@/'$(grep UpgradeAutoClose ~/.config/apt-notifierrc | cut -f2 -d=)'/' "$TMP"/DIALOG


    gtkdialog --file="$TMP"/DIALOG >> "$TMP"/output

    grep -q EXIT=.*OK.* "$TMP"/output

    if [ "$?" -eq 0 ];
      then
        if [ $(grep UpgradeType_upgrade=.*true.*      "$TMP"/output) ]; then sed -i 's/UpgradeType=dist-upgrade/UpgradeType=upgrade/' ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeType_dist-upgrade=.*true.* "$TMP"/output) ]; then sed -i 's/UpgradeType=upgrade/UpgradeType=dist-upgrade/' ~/.config/apt-notifierrc; fi
        if [ $(grep LeftClickViewAndUpgrade=.*true.*  "$TMP"/output) ]; then sed -i 's/LeftClick=Synaptic/LeftClick=ViewAndUpgrade/'  ~/.config/apt-notifierrc; fi
        if [ $(grep LeftClickSynaptic=.*true.*        "$TMP"/output) ]; then sed -i 's/LeftClick=ViewAndUpgrade/LeftClick=Synaptic/'  ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeAssumeYes=.*false.*        "$TMP"/output) ]; then sed -i 's/UpgradeAssumeYes=true/UpgradeAssumeYes=false/' ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeAssumeYes=.*true.*         "$TMP"/output) ]; then sed -i 's/UpgradeAssumeYes=false/UpgradeAssumeYes=true/' ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeAutoClose=.*false.*        "$TMP"/output) ]; then sed -i 's/UpgradeAutoClose=true/UpgradeAutoClose=false/' ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeAutoClose=.*true.*         "$TMP"/output) ]; then sed -i 's/UpgradeAutoClose=false/UpgradeAutoClose=true/' ~/.config/apt-notifierrc; fi
      else
        :
    fi

    rm -rf "$TMP"

    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(['sh %s' % script_file.name],shell=True).wait()
    check_updates()

# Define the command to run when left clicking on the Tray Icon
def left_click():
    if text.startswith( "0" ):
        start_synaptic()
    else:
        """Test ~/.config/apt-notifierrc for LeftClickViewAndUpgrade"""
        command_string = "cat " + rc_file_name + " | grep -q LeftClick=ViewAndUpgrade"
        exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
        if exit_state == 0:
            viewandupgrade()
        else:
            start_synaptic()

# Define the action when left clicking on Tray Icon
def left_click_activated(reason):
    if reason == QtGui.QSystemTrayIcon.Trigger:
        left_click()

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

def add_rightclick_actions():
    ActionsMenu.clear()
    """Test ~/.config/apt-notifierrc for LeftClickViewAndUpgrade"""
    command_string = "cat " + rc_file_name + " | grep -q LeftClick=ViewAndUpgrade"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state == 0:
        process_updates_action = ActionsMenu.addAction("Upgrade using Synaptic")
        AptNotify.connect(process_updates_action, QtCore.SIGNAL("triggered()"), start_synaptic)
    else:
        process_updates_action = ActionsMenu.addAction("View and Upgrade")
        AptNotify.connect(process_updates_action, QtCore.SIGNAL("triggered()"), viewandupgrade)
    add_apt_notifier_help_action()
    add_synaptic_help_action()
    add_quit_action()
    add_aptnotifier_prefs_action()

def add_hide_action():
    ActionsMenu.clear()
    if icon_config == "show":
        hide_action = ActionsMenu.addAction("Hide until updates available")
        AptNotify.connect(hide_action,QtCore.SIGNAL("triggered()"),set_noicon)
    add_apt_notifier_help_action()
    add_synaptic_help_action()
    add_quit_action()
    add_aptnotifier_prefs_action()

def add_quit_action():
    ActionsMenu.addSeparator()
    quit_action = ActionsMenu.addAction(QuitIcon,"Quit Apt-Notifier")
    AptNotify.connect(quit_action, QtCore.SIGNAL("triggered()"), AptNotify.exit)

def add_apt_notifier_help_action():
    ActionsMenu.addSeparator()
    apt_notifier_help_action = ActionsMenu.addAction(HelpIcon,"Apt-Notifier Help")
    apt_notifier_help_action.triggered.connect(open_apt_notifier_help)
    
def open_apt_notifier_help():
    subprocess.Popen(['xdg-open http://www.mepiscommunity.org/doc_mx/mxapps.html#notify'],shell=True)
    
def add_synaptic_help_action():
    ActionsMenu.addSeparator()
    synaptic_help_action = ActionsMenu.addAction(HelpIcon,"Synaptic Help")
    synaptic_help_action.triggered.connect(open_synaptic_help)
    
def open_synaptic_help():
    subprocess.Popen(['xdg-open http://www.mepiscommunity.org/doc_mx/synaptic.html'],shell=True)

def add_aptnotifier_prefs_action():
    ActionsMenu.addSeparator()
    aptnotifier_prefs_action =  ActionsMenu.addAction("Apt Notifier Preferences")
    AptNotify.connect(aptnotifier_prefs_action,QtCore.SIGNAL("triggered()"), aptnotifier_prefs)

# General application code	
def main():
    # Define Core objects, Tray icon and QTimer 
    global AptNotify
    global AptIcon
    global QuitIcon
    global icon_config
    global quit_action    
    global Timer
    global initialize_aptnotifier_prefs
    initialize_aptnotifier_prefs()
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
    HelpIcon = QtGui.QIcon("/usr/share/icons/oxygen/22x22/apps/help-browser.png")
    QuitIcon = QtGui.QIcon("/usr/share/icons/oxygen/22x22/actions/system-shutdown.png")
    # Create the right-click menu and add the Tooltip text
    global ActionsMenu
    ActionsMenu = QtGui.QMenu()
    AptIcon.connect( AptIcon, QtCore.SIGNAL( "activated(QSystemTrayIcon::ActivationReason)" ), left_click_activated)
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
