#!/usr/bin/python3
# version 1.0
#
# first program to learn python and Gtk
# Capture images and create a timelapse video using an RPI camera
# requires: ffmpeg, raspistill (optional gthumb for triage)
# antoine@ginies.org
#

import gi
from PIL import Image
import configparser
import subprocess
import sys
import io
import time
import threading
import os.path

gi.require_version('Gst', '1.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('GstVideo', '1.0')
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, GObject, Gst, GstVideo

Gst.init(None)
video_dev = "/dev/video0"

def read_config():
    config = configparser.ConfigParser()
    STARTCONFIGFILE = '/etc/config.ini'
    if os.path.isfile(STARTCONFIGFILE):
        print("reading /etc/config.ini")
        config.read(STARTCONFIGFILE)
#        config.close()
    else:
        CONFIGFILE = 'config.ini'
        if os.path.isfile('config.ini'):
            print("reading config.ini")
            config.read('config.ini')
            return config
        else:
            print("No config creating one!")
            f = open("config.ini","w+")
            config.read('config.ini')
            if config.has_section("all") != True:
                config.add_section('all')
            config.set('all', 'verbose', "false")
            config.set('all', 'configfile', 'config.ini')
            config.set('all', 'working_dir', '/tmp/')
            config.set('all', 'rotation', '180')
            #config.set('all', 'raspistill', '/usr/bin/raspistill')
            config.set('all', 'image_name', 'image')
            config.set('all', 'width', '1920')
            config.set('all', 'height', '1080')
            config.set('all', 'quality', '10')
            config.set('all', 'encoding', 'jpg')
            config.set('all', 'timelapse', '3000')
            config.set('all', 'extra', '')
            config.write(f)
            f.close()
            return config


class DisplayConf(Gtk.Window):
    def __init__(self, parent):
        Gtk.Window.__init__(self, title="Rpi Camera serrings", transient_for=parent)

        self.set_default_size(640, 480)
        self.set_border_width(10)

        def show_help(button):
            #self.help_button.set_sensitive(False)
            win = Gtk.Window(title="Raspistill help", transient_for=parent)
            win.set_default_size(800, 700)
            win.set_border_width(10)

            # get help
            cmd = "raspistill --help"
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            rc = proc.wait()
            outs, errs = proc.communicate(timeout=2)
            textview = Gtk.TextView()
            textbuffer = textview.get_buffer()
            textview.set_editable(False)
            scrolled = Gtk.ScrolledWindow()
            scrolled.add(textview)
            end_iter = textbuffer.get_end_iter()
            textbuffer.insert(end_iter, outs.decode("utf8"))

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, border_width=12)
            box.pack_start(scrolled, True, True, 0)
            win.add(box)
            win.show_all()
 
        def on_clicked_ok(button_ok):
            print("saving file")
            fp = open(entry_info_config.get_text(), 'w')

            if button_verbose.get_active() == 1:
                print("true")
                config.set('all', 'verbose', "true")
            else:
                print("false")
                config.set('all', 'verbose', "false")
            config.set('all', 'configfile', entry_info_config.get_text())
            config.set('all', 'working_dir', entry_working_dir.get_text())
            config.set('all', 'rotation', entry_rot.get_text())
            #config.set('all', 'raspistill', entry_raspistill.get_text())
            config.set('all', 'image_name', entry_image_name.get_text())
            config.set('all', 'width', entry_width.get_text())
            config.set('all', 'height', entry_height.get_text())
            config.set('all', 'quality', entry_quality.get_text())
            config.set('all', 'encoding', entry_encoding.get_text())
            config.set('all', 'timelapse', entry_timelapse.get_text())
            config.set('all', 'extra', entry_extra.get_text())
            config.write(fp)
            fp.close()
            self.destroy()


        def on_clicked_cancel(button_cancel):
            print("cancel")
            self.destroy()

        def on_button_ckeck_verbose(button, button_verbose):
            if button.get_active():
                state = "on"
                print("Verbose on")
            else:
                print("Verbose off")

        def on_file_clicked(widget):
            dialog = Gtk.FileChooserDialog(
                title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            )

            filter_ini = Gtk.FileFilter()
            filter_ini.set_name("ini file")
            filter_ini.add_pattern("*.ini")
            dialog.add_filter(filter_ini)

            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                print("Open clicked")
                print("File selected: " + dialog.get_filename())
                entry_info_config.set_text(dialog.get_filename())
            elif response == Gtk.ResponseType.CANCEL:
                print("Cancel clicked")

            dialog.destroy()


        #
        # read from config file
        config = read_config()

        self.help_button = Gtk.Button(label="raspistill Help")
        self.help_button.connect("clicked", show_help)
 

        box_info_config = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_info_config = Gtk.Entry()
        label_info_config = Gtk.Label("Path to config file")
        if config.has_option('all', 'configfile'):
            entry_info_config.set_text(config.get('all', 'configfile'))
#        else:
#            entry_info_config.set_text("config.ini")
        file_info_config = Gtk.Button(label="Choose File")
        file_info_config.connect("clicked", on_file_clicked)

#        box_raspistill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
#        entry_raspistill = Gtk.Entry()
#        label_raspistill = Gtk.Label("Path to raspistill")
#        if config.has_option('all', 'raspistill'):
#            entry_raspistill.set_text(config.get('all', 'raspistill'))
#        else:
#            entry_raspistill.set_text("/usr/bin/raspistill")

        # rotate or not
        box_rot = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_rot = Gtk.Entry()
        label_rot = Gtk.Label("Image Rotation")
        if config.has_option('all', 'rotation'):
            entry_rot.set_text(config.get('all', 'rotation'))
        else:
            entry_rot.set_text("0")

        box_width = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_width = Gtk.Entry()
        label_width = Gtk.Label("Image Width")
        if config.has_option('all', 'width'):
            entry_width.set_text(config.get('all', 'width'))
        else:
            entry_width.set_text("1920")

        box_height = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_height = Gtk.Entry()
        label_height = Gtk.Label("Image Height")
        if config.has_option('all', 'height'):
            entry_height.set_text(config.get('all', 'height'))
        else:
            entry_height.set_text("1080")

        box_timelapse = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_timelapse = Gtk.Entry()
        label_timelapse = Gtk.Label("Time between captures (in ms)")
        if config.has_option('all', 'timelapse'):
            entry_timelapse.set_text(config.get('all', 'timelapse'))
        else:
            entry_timelapse.set_text("3000")

        box_quality = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_quality = Gtk.Entry()
        label_quality = Gtk.Label("Quality")
        if config.has_option('all', 'quality'):
            entry_quality.set_text(config.get('all', 'quality'))
        else:
            entry_quality.set_text("10")

        box_verbose = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label_verbose = Gtk.Label("Verbose")
        button_verbose = Gtk.CheckButton()
        if config.has_option('all', 'verbose'):
            if config.get('all', 'verbose') == "true":
                button_verbose.set_active("True")
        button_verbose.connect("toggled", on_button_ckeck_verbose, "1")

        box_encoding = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_encoding = Gtk.Entry()
        label_encoding = Gtk.Label("Encoding format")
        if config.has_option('all', 'encoding'):
            entry_encoding.set_text(config.get('all', 'encoding'))
        else:
            entry_encoding.set_text("jpg")

        box_image_name = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_image_name = Gtk.Entry()
        label_image_name = Gtk.Label("Image Name (prefix)")
        if config.has_option('all', 'image_name'):
            entry_image_name.set_text(config.get('all', 'image_name'))
        else:
            entry_image_name.set_text('image_' + format(percent) + '04d.jpg')

        box_working_dir = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_working_dir = Gtk.Entry()
        label_working_dir = Gtk.Label("Working Directory")
        if config.has_option('all', 'working_dir'):
            entry_working_dir.set_text(config.get('all', 'working_dir'))
        else:
            entry_working_dir.set_text("/tmp/")

        box_extra = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        entry_extra = Gtk.Entry()
        label_extra = Gtk.Label("Extra Options")
        if config.has_option('all', 'extra'):
            entry_extra.set_text(config.get('all', 'extra'))
        else:
            entry_extra.set_text("")


        box_ok_cancel= Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_ok = Gtk.Button.new_with_mnemonic("_Ok")
        button_ok.connect("clicked", on_clicked_ok)
        button_cancel = Gtk.Button.new_with_mnemonic("_Cancel")
        button_cancel.connect("clicked", on_clicked_cancel)

        box_info_config.pack_start(label_info_config, False, False, 0)
        box_info_config.pack_start(entry_info_config, False, False, 0)
        box_info_config.pack_end(file_info_config, False, False, 0)
 #       box_raspistill.pack_start(label_raspistill, False, False, 0)
 #       box_raspistill.pack_end(entry_raspistill, False, False, 0)
        box_working_dir.pack_start(label_working_dir, False, False, 0)
        box_working_dir.pack_end(entry_working_dir, False, False, 0)
        box_rot.pack_start(label_rot, False, False, 0)
        box_rot.pack_end(entry_rot, False, False, 0)
        box_height.pack_start(label_height, False, False, 0)
        box_height.pack_end(entry_height, False, False, 0)
        box_width.pack_start(label_width, False, False, 0)
        box_width.pack_end(entry_width, False, False, 0)
        box_image_name.pack_start(label_image_name, False, False, 0)
        box_image_name.pack_end(entry_image_name, False, False, 0)
        box_encoding.pack_start(label_encoding, False, False, 0)
        box_encoding.pack_end(entry_encoding, False, False, 0)
        box_verbose.pack_start(label_verbose, False, False, 0)
        box_verbose.pack_end(button_verbose, False, False, 0)
        box_ok_cancel.pack_start(button_cancel, False, False, 0)
        box_ok_cancel.pack_end(button_ok, False, False, 0)
        box_timelapse.pack_start(label_timelapse, False, False, 0)
        box_timelapse.pack_end(entry_timelapse, False, False, 0)
        box_extra.pack_start(label_extra, False, False, 0)
        box_extra.pack_end(entry_extra, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_spacing(20)
        self.add(vbox)
        vbox.pack_start(self.help_button, False, False, 0)

        vboxconf = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
 #       vbox.pack_start(box_raspistill, False, False, 0)
        vboxconf.pack_start(box_info_config, False, False, 0)
        vboxconf.pack_start(box_working_dir, False, False, 0)
        vboxconf.pack_start(box_image_name, False, False, 0)
        frameconf = Gtk.Frame()
        frameconf.add(vboxconf)
        frameconf.show()

        vboximg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vboximg.pack_start(box_rot, False, False, 0)
        vboximg.pack_start(box_height, False, False, 0)
        vboximg.pack_start(box_width, False, False, 0)
        vboximg.pack_start(box_encoding, False, False, 0)
        vboximg.pack_start(box_quality, False, False, 0)
        frameimage = Gtk.Frame()
        frameimage.add(vboximg)
        frameimage.show()

        vboxmore = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vboxmore.pack_start(box_timelapse, False, False, 0)
        vboxmore.pack_start(box_extra, False, False, 0)
        vboxmore.pack_start(box_verbose, False, False, 0)
        framemore = Gtk.Frame()
        framemore.add(vboxmore)
        framemore.show()

        vbox.add(frameconf)
        vbox.add(frameimage)
        vbox.add(framemore)
        vbox.pack_end(box_ok_cancel, False, False, 0)
        self.show_all()


class LogInterFace(Gtk.Window):
    def __init__(self, command):

        Gtk.Window.__init__(self,
                title="Log Interface",
                default_width=500,
                default_height=400,
                )
        self.cancellable = Gio.Cancellable()

        self.start_button = Gtk.Button(label="Show log")
        self.start_button.connect("clicked", self.on_start_clicked)

        textview = Gtk.TextView()
        self.textbuffer = textview.get_buffer()
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(textview)
        self.command = command
        progress = Gtk.ProgressBar(show_text=True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, border_width=12)
        box.pack_start(self.start_button, False, True, 0)
        box.pack_start(progress, False, True, 0)
        box.pack_start(scrolled, True, True, 0)

        self.add(box)
 
    def autoscroll(self, *args):
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def append_text(self, text):
        iter_ = self.textbuffer.get_end_iter()
        self.textbuffer.insert(iter_, "[%s] %s\n" % (str(time.time()), text))

class MainBox(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="RPI Camera")

        self.set_default_size(320, 280)
        self.set_border_width(20)

        self.img = Image.open('cover.jpg')
        newimg = self.img.resize((200, 200))
        newimg.save('/tmp/_cover.jpg')
        self.live = Gtk.Image()
        self.live.set_from_file("/tmp/_cover.jpg")
        self.live_on_button = Gtk.Button(label="Live On")
        self.live_on_button.connect("clicked", self.start_live)
        self.live_off_button = Gtk.Button(label="Live Off")
        self.live_off_button.set_sensitive(False)
        self.live_off_button.connect("clicked", self.stop_live)
        # vbox contains status and live
        self.vboxlive = Gtk.Box()
        self.vboxlive.set_orientation(Gtk.Orientation.VERTICAL)
        self.vboxlive.set_spacing(10)
        hboxlive = Gtk.Box()
        hboxlive.set_orientation(Gtk.Orientation.HORIZONTAL)
        hboxlive.set_spacing(10)
        hboxlive.pack_start(self.live_on_button, False, False, 0)
        hboxlive.pack_end(self.live_off_button, False, False, 0)

        # Create DrawingArea for video widget
        self.drawingarea = Gtk.DrawingArea()
        #self.drawingarea.set_size_request(400, 300)
       
        # Needed or else the drawing area will be really small (1px)
        self.drawingarea.set_hexpand(True)
        self.drawingarea.set_vexpand(True)
        #self.vboxlive.add(self.drawingarea)
        self.vboxlive.add(hboxlive)
        self.vboxlive.add(self.live)

        #info
        info = Gtk.Label()
        info.set_text("\nCreate a Timelapse based on RPI camera captures\n")

        # current status
        self.status = Gtk.Label()
        self.status.set_text("Capture OFF")
        self.nb_capture = Gtk.Label()
        self.c_button = Gtk.Button(label="Capture")
        self.c_button.set_tooltip_text("Start capturing timelapse")
        self.c_button.connect("clicked", self.start_capture)
        self.s_button = Gtk.Button(label="Stop")
        self.s_button.set_tooltip_text("Stop to capture timelapse")
        self.s_button.set_sensitive(False)
        self.s_button.connect("clicked", self.stop_capture)
        self.settings_button = Gtk.Button(label="Settings")
        self.settings_button.set_tooltip_text("Configure all options for the Timelapse")
        #https://developer.gnome.org/gnome-devel-demos/stable/tooltip.py.html.en
        # with a tooltip with a given text in the Pango markup language
        #BLAL.set_tooltip_markup("Open an <i>existing</i> file")        
        self.settings_button.connect("clicked", self.on_set_conf)
        self.settings_button.set_sensitive(True)

        vbox = Gtk.Box()
        vbox.set_orientation(Gtk.Orientation.VERTICAL)
        vbox.set_spacing(10)
        self.add(vbox)

        hboxinfo =Gtk.Box()
        hboxinfo.set_orientation(Gtk.Orientation.HORIZONTAL)
        hboxinfo.set_spacing(10)
        hboxinfo.pack_start(info, True, True, 10)
        frameinfo = Gtk.Frame()
        frameinfo.add(hboxinfo)
        frameinfo.show()

        # vbox contains status and live
        vboxs = Gtk.Box()
        vboxs.set_orientation(Gtk.Orientation.VERTICAL)
        vboxs.set_spacing(10)
        vboxs.pack_start(self.status, True, False, 1)
        self.nb_capture.set_visible(False)
        vboxs.pack_start(self.nb_capture, False, False, 0)

        framestatus = Gtk.Frame()
        framestatus.set_label("Timelapse Status")
        framestatus.add(vboxs)
        framestatus.show()

        self.framelive = Gtk.Frame()
        self.framelive.set_label("Live (Off)")
        self.framelive.set_tooltip_text("Live ON/OFF | Capture (ON/OFF)")
        self.framelive.add(self.vboxlive)
        self.framelive.show()

        # create a hboxbut for button line and frame
        hboxbut = Gtk.Box()
        hboxbut.set_spacing(10)
        hboxbut.pack_end(self.settings_button, True, True, 0)
        hboxbut.pack_end(self.c_button, True, True, 0)
        hboxbut.pack_end(self.s_button, True, True, 0)
        framebut = Gtk.Frame()
        framebut.set_label("Command")
        framebut.add(hboxbut)
        framebut.show()

        self.hboxrender = Gtk.Box()
        self.hboxrender.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.hboxrender.set_spacing(10)
        self.render_button = Gtk.Button(label="Render")
        self.render_button.connect("clicked", self.render_timelapse)
        self.stop_render_button = Gtk.Button(label="Stop Rendering")
        self.stop_render_button.connect("clicked", self.stop_render)
        self.stop_render_button.set_sensitive(False)
        self.choose_image_button = Gtk.Button(label="Gthumb")
        self.choose_image_button.connect("clicked", self.launch_gthumb)
        self.render_spinner= Gtk.Spinner()
        self.hboxrender.pack_start(self.render_button, False, False, 0)
        self.hboxrender.pack_start(self.stop_render_button, False, False, 0)
        self.hboxrender.pack_start(self.choose_image_button, False, False, 0)
        self.hboxrender.pack_end(self.render_spinner, True, False, 0)
        self.render_button.set_sensitive(False)
        self.render_button.set_tooltip_text("Create the video based on the capture")
        framerender = Gtk.Frame()
        framerender.set_label("Create the Timelapse video")
        framerender.add(self.hboxrender)
        framerender.show()

        vbox.add(frameinfo)
        vbox.add(framestatus)
        vbox.add(self.framelive)
        vbox.add(framebut)
        vbox.add(framerender)

        self.source_id = 0
        self.count = 0

        if os.path.isfile("/usr/bin/raspistill") == False:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="/usr/bin/raspistill is not present, please install it.",
            )
            dialog.run()
            dialog.destroy()

    def launch_gthumb(self, button):
        print("Launch Gthumb")
        if os.path.isfile("/usr/bin/gthumb"):
            config = read_config()
            self.working_dir = config.get('all', 'working_dir')
            cmd = "/usr/bin/gthumb " + self.working_dir
            self.sp = subprocess.Popen(cmd, cwd=self.working_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="/usr/bin/gthumb is not present, please install it.",
            )
            dialog.run()
            dialog.destroy()

    def start_live(self, button):
       # Create GStreamer pipeline
        self.vboxlive.remove(self.live)
        self.vboxlive.add(self.drawingarea)
        self.framelive.set_label("Live (On)")
        self.live_on_button.set_sensitive(False)
        self.live_off_button.set_sensitive(True)
        self.c_button.set_sensitive(False)
        self.pipeline = Gst.parse_launch("v4l2src device=" + video_dev + " ! tee name=tee ! queue name=videoqueue ! deinterlace ! xvimagesink")

        # Create bus to get events from GStreamer pipeline
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', self.on_eos)
        bus.connect('message::error', self.on_error)

        # This is needed to make the video output in our DrawingArea:
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.on_sync_message)
        self.runvideo()

    def stop_live(self, button):
        self.framelive.set_label("Live (Off)")
        self.vboxlive.remove(self.drawingarea)
        self.vboxlive.add(self.live)
        self.live_on_button.set_sensitive(True)
        self.live_off_button.set_sensitive(False)
        self.c_button.set_sensitive(True)
        self.pipeline.set_state(Gst.State.NULL)

    def runvideo(self):
        self.show_all()
        self.xid = self.drawingarea.get_property('window').get_xid()
        self.pipeline.set_state(Gst.State.PLAYING)
        #Gtk.main()

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            #print('prepare-window-handle')
            msg.src.set_property('force-aspect-ratio', True)
            msg.src.set_window_handle(self.xid)

    def on_eos(self, bus, msg):
        print('on_eos(): seeking to start of video')
        self.pipeline.seek_simple( Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())

    def Update_rendering(self):
        if self.sp.poll() is None:
            print("Rendering in progress... ")
            return True
        else:
            print("Rendering Finished")
            print(self.sp.stdout)
            print(self.sp.stderr)
            self.render_button.set_sensitive(True)
            self.render_spinner.stop()
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Video available: " + self.working_dir + "/output.mp4",
            )
            dialog.run()
            dialog.destroy()
            self.stop_render_button.set_sensitive(False)
            return False

    def render_timelapse(self, button):
        #ffmpeg -r 10 -pattern_type glob -i "*.jpg" -s 1920x1080 -vcodec libx264 output.mp4
        print('try to do rendering!')
        config = read_config()
        self.working_dir = config.get('all', 'working_dir')
        encoding = config.get('all', 'encoding')
        width = config.get('all', 'width')
        height = config.get('all', 'height')
        self.image_name = config.get('all', 'image_name')

        cmd = "ffmpeg -y -r 10 -pattern_type glob -i \"" + self.working_dir + "/" + self.image_name + "*." + encoding + "\" " + " -s " + width + "x" + height + " -vcodec libx264 " + self.working_dir + "/output.mp4"
        if os.path.isfile("/usr/bin/ffmpeg"):
            print(cmd)
            self.sp = subprocess.Popen(cmd, cwd=self.working_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.render_button.set_sensitive(False)
            self.stop_render_button.set_sensitive(True)
            self.c_button.set_sensitive(False)
            self.render_spinner.start()
            self.source_id = GLib.timeout_add(2000, self.Update_rendering)

        else:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="/usr/bin/ffmpeg is not present, please install it.",
            )
            dialog.run()
            dialog.destroy()

    def stop_render(self, button):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Are you Sure you want to stop Rendering in Video?",
        )
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            GLib.source_remove(self.source_id)
            # TOFIX
            pid = self.sp.pid
            cmd = "kill -9 " + str(pid)
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            rc = proc.wait()
            try:
                outs, errs = proc.communicate(timeout=2)
            except TimeoutExpired:
                proc.kill()
                outs, errs = proc.communicate()
            # enable rendering
            self.c_button.set_sensitive(True)
            self.render_button.set_sensitive(True)
            self.stop_render_button.set_sensitive(False)
            self.render_spinner.stop()
        elif response == Gtk.ResponseType.NO:
            print("Cancel")
        dialog.destroy()


    def Update_info(self, timer):
      c = timer.count + 1
      timer.count = c
      # number of capture start from 1
      nb = c + 1
      print("Update to image image_" + str(c).zfill(4) + '.jpg')
      self.nb_capture.set_text("Number of Captures (every " + str(int(self.timelapse)/1000) +  "s) : " + str(nb))
      imagename= self.working_dir + "/" + self.image_name + str(c).zfill(4) + "." + self.encoding
      if os.path.isfile(imagename):
          self.img = Image.open(imagename)
          sizeh = int(400/self.ratio)
          newimg = self.img.resize((400, sizeh))
          newimg.save(self.working_dir + "/_live_record_rpi." + self.encoding)
          self.live.set_from_file(self.working_dir + "/_live_record_rpi." + self.encoding)
      else:
          print("image not ready... bypassing")
      return True

    def start_capture(self, button):
        #raspistill -rot 180 --timelapse 3000 -o img_%04d.jpg --width 1920 --height 1080 --verbose --focus --encoding jpg --quality 10 -t 0
        if self.status.get_text() == "Capture ON":
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Capture is already on going...",
                )
            dialog.run()
            dialog.destroy()
        else:
            config = read_config()
            rot= config.get('all', 'rotation')
            raspistill = config.get('all', 'raspistill')
            self.image_name = config.get('all', 'image_name')
            width = config.get('all', 'width')
            height = config.get('all', 'height')
            quality = config.get('all', 'quality')
            self.encoding = config.get('all', 'encoding')
            self.timelapse = config.get('all', 'timelapse')
            self.working_dir = config.get('all', 'working_dir')
            extra = config.get('all', 'extra')
            # be sure working dir exist
            if not os.path.exists(self.working_dir):
                os.makedirs(self.working_dir)
 
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="All previous images will be deleted from this directory. Are you Sure you want to do this ?\n\n" + self.working_dir,
            )
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                cmd = "rm -rvf *." + self.encoding
                proc = subprocess.Popen(cmd, cwd=self.working_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                rc = proc.wait()
                try:
                    outs, errs = proc.communicate(timeout=2)
                except TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()

                self.live_on_button.set_sensitive(False)
                self.live_off_button.set_sensitive(False)
                self.vboxlive.remove(self.drawingarea)
                self.vboxlive.add(self.live)
                self.c_button.set_sensitive(False)
                self.settings_button.set_sensitive(False)
                self.s_button.set_sensitive(True)
                self.nb_capture.set_visible(True)
                print('Start Capturing')
                self.status.set_text("Capture ON")

                if config.get('all', 'verbose') == "true":
                    verbose = "--verbose"
                else:
                    verbose = ""
                command = raspistill + " -rot " + rot + " --timelapse " + self.timelapse + " -o " + self.image_name + str(chr(37)) +"04d." + self.encoding + " --width " + width + " --height " + height + " --quality " + quality +  " -t 0" + " --encoding " + self.encoding + " " + extra
                #+ "2> /tmp/_datafile"

                self.sp = subprocess.Popen(command, cwd=self.working_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.ratio = float(int(width)/int(height))
                # wait for first image
                self.live.set_from_file("/usr/share/icons/gnome/48x48/status/image-loading.png")
                self.framelive.set_label("Capture (On)")
                # wait for first image...
                time.sleep(2)
                self.source_id = GLib.timeout_add(int(self.timelapse), self.Update_info, self)

            elif response == Gtk.ResponseType.NO:
                print("cancel")

            dialog.destroy()

    def stop_capture(self,button):
        if self.status.get_text() == "Capture OFF":
            print("Noting to do")
        else:
            print('Stop')
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Are you Sure you want to stop Timelapse Recording?",
            )
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                GLib.source_remove(self.source_id)
                pid = self.sp.pid
                cmd = "kill -9 " + str(pid)
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                rc = proc.wait()
                try:
                    outs, errs = proc.communicate(timeout=2)
                except TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()
                self.status.set_text("Capture OFF")
                self.framelive.set_label("Live (Off)")
                self.c_button.set_sensitive(True)
                self.settings_button.set_sensitive(True)
                self.s_button.set_sensitive(False)
                self.live_on_button.set_sensitive(True)
                # enable rendering
                self.render_button.set_sensitive(True)
                self.stop_render_button.set_sensitive(False)
            elif response == Gtk.ResponseType.NO:
                print("Cancel")
    
            dialog.destroy()

    def on_set_conf(self, widget):
        dialog = DisplayConf(self)


# MAIN
window = MainBox()
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()
