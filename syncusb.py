from os.path import exists
from os.path import ismount
import os
import logging
from time import localtime
from feedback import led_warning, led_sync_success
from subprocess import call

def syncusb():

    local_logdir = "log"
    local_recdir = "records"
    remote_dir = "/media/pi/STICKERL/LIEHSE"
    usb_path = "/media/pi/STICKERL"

    # First, establish that the USB storage is connected, accessible
    # and we have the log and records directory in place:
    usb_connected = ismount(usb_path)
    logging.info("is mount (%s): %s" % (usb_path, usb_connected))

    if not usb_connected:
        logging.warning("USB not connected, aborting.")
        led_warning()
        return()

    logging.debug("USB connected.")

    if not exists(remote_dir):
        try:
            os.mkdir(remote_dir)
            logging.info("Created %s" % remote_dir)
        except OSError:
            logging.warning("Creation of LIEHSE failed.")
            led_warning()
            return()

    if not exists(remote_dir + "/log"):
        try:
            os.mkdir(remote_dir + "/log")
            logging.info("Created %s." % remote_dir + "/log")
        except OSError:
            logging.warning("Creation of %s" % remote_dir + "/log failed.")
            led_warning()
            return()
            
    logging.debug("log directory exists.")

    if not exists(remote_dir + "/records"):
        try:
            os.mkdir(remote_dir + "/records")
            logging.info("Created %s." % remote_dir + "/records")
        except OSError:
            logging.warning("Creation of %s" % remote_dir + "/records failed.")
            led_warning()
            return()

    logging.debug("records directory exists.")
    logging.debug("Starting to sync.")

    # do the syncing:
    batcmd = "rsync -rtvh " + local_logdir + " " + remote_dir
    logging.debug(batcmd + "...")
    call([batcmd], shell = True)

    batcmd = "rsync -rtvh " + local_recdir + " " + remote_dir
    logging.debug(batcmd + "...")
    call([batcmd], shell = True)







