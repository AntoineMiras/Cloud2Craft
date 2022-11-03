# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 11:32:27 2022

@author: antoi
"""

# =============================================================================
# Modules
# =============================================================================

import sys

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread

from PyQt5.uic import loadUi

from PyQt5.QtWidgets import (QMainWindow, QApplication, QFileDialog, QMessageBox)

from PyQt5.QtGui import QIcon

import os

from open3d import geometry, utility

from mcpi.minecraft import Minecraft

import numpy as np

import laspy

import subprocess

from time import sleep, time

# =============================================================================
# Custom Modules
# =============================================================================

from c2c_Colorizer2 import colorizer

# =============================================================================
# Func
# =============================================================================

def closest_color(rgb, col_lst):
    """
    Return the color from a given list that is the closest of the real color

    Parameters
    ----------
    rgb : TYPE TUPLE
        real color.
    col_lst : TYPE LIST
        given color list.

    Returns
    -------
    TYPE TUPLE
        Closest Color.

    """
    r, g, b = rgb
    r *= 256
    g *= 256
    b *= 256
    color_diffs = []

    for color in col_lst:
        cr, cg, cb = color
        color_diff = np.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        color_diffs.append((color_diff, color))
    return min(color_diffs)[1]


def save_param(instance):
    """Save the user preferences in a file"""
    txt = open(parent_dir + "\\user_pref.txt", "w+")
    txt.write("path-->" + instance.ser_path.text().rstrip().replace("\\", "/") + "\n" +
              "port-->" + instance.port.text().rstrip() + "\n" +
              "start-->" + str(True if instance.start.isChecked() else False) + "\n" +
              "tp-->" + str(True if instance.tp.isChecked() else False))
    txt.close()


def read_param(instance):
    """Retrieve the user preferences"""
    txt = open(parent_dir + "\\user_pref.txt", "r+")
    lines = txt.readlines()
    txt.close()

    for line in lines:
        if "path" in line:
            instance.ser_path.setText(line.split("-->")[-1].rstrip("\n"))
        if "port" in line:
            instance.port.setText(line.split("-->")[-1].rstrip("\n"))
        if "start" in line:
            instance.start.setChecked(True if "True" in line else False)
        if "tp" in line:
            instance.tp.setChecked(True if "True" in line else False)


def create_bat(instance):
    """Create a batch file to quick launch the server"""
    path = instance.ser_path.text()
    bat = open(path.replace(path.split("/")[-1], "launch serv.bat"), "w+")
    bat.write('java -jar "' + path + '"')
    bat.close()


def mod_serv_properties(path, port):
    """Edit the server properties"""
    try:
        prop = open(path.replace(path.split("/")[-1], "server.properties"), "r")
        lines = prop.readlines()
        prop.close()

        propp = open(path.replace(path.split("/")[-1], "server.properties"), "w")
        for line in lines:
            if "server-port" not in line:
                propp.write(line)
            else:
                propp.write(line.split("=")[0] + "=" + port + "\n")
        propp.close()
    except Exception as e:
        print(e)
        QMessageBox.critical(MAINWINDOW, 'Error',
                             "Server properties unreachable: the path is incorrect or the file is missing")


def recursive_split(x_min, y_min, x_max, y_max, max_x_size, max_y_size):
    x_size = x_max - x_min
    y_size = y_max - y_min

    if x_size > max_x_size:
        left = recursive_split(x_min, y_min, x_min + (x_size // 2), y_max, max_x_size, max_y_size)
        right = recursive_split(x_min + (x_size // 2), y_min, x_max, y_max, max_x_size, max_y_size)
        return left + right
    elif y_size > max_y_size:
        up = recursive_split(x_min, y_min, x_max, y_min + (y_size // 2), max_x_size, max_y_size)
        down = recursive_split(x_min, y_min + (y_size // 2), x_max, y_max, max_x_size, max_y_size)
        return up + down
    else:
        return [(x_min, y_min, x_max, y_max)]


def tuple_size(string):
    try:
        return tuple(map(float, string.split("x")))
    except Exception as e:
        print(e)
        raise ValueError("Size must be in the form of numberxnumber eg: 50.0x65.14")


def is_server_running():
    """Check if the server is runing"""
    try:
        mc = Minecraft.create(address="localhost", port=4711)
        return mc
    except Exception as e:
        print(e)
        return False

# =============================================================================
# Ui / Thread
# =============================================================================

class init_serv(QObject):
    finished = pyqtSignal()
    error = pyqtSignal()

    def run(self):
        try:
            dirr = MAINWINDOW.ser_path.text() #on recup le chemin du serv
            pipe = subprocess.Popen("launch serv.bat",
                                    cwd=dirr.replace(dirr.split("/")[-1], ""),
                                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                                    ) #on lance la commande pour créer un serveur
            while not MAINWINDOW.mc: #tant que le serveur n'est pas lancé
                sleep(3) #petite pause
                if pipe.poll() == None:
                    MAINWINDOW.mc = is_server_running() #on regarde si il fonctionne
                else:
                    self.error.emit()
                    return None
            self.finished.emit() #on dit que le thread est finito
            return None #on retourne rien

        except Exception as e:
            print(e)
            self.error.emit()
            return None

    def stop(self):
        self.threadactive = False
        self.wait()


class load_points(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    maxi = pyqtSignal(int)

    def __init__(self, mc, fname, size, pts_it, vsize, xoff, yoff, zoff, pPos, cpalette):
        super(load_points, self).__init__()
        self.mc = mc
        self.fname = fname
        self.size = size
        self.pts_it = pts_it
        self.vsize = vsize
        if pPos:
            try:
                xoff, zoff, yoff = mc.player.getPos()
            except:
                QMessageBox.critical(MAINWINDOW, 'Error',
                                     "Player position couldn't be recovered, please retry.")

                self.finished.emit()
                return None

        self.xoff = xoff
        self.yoff = yoff
        self.zoff = zoff
        self.stop = False
        self.blockPalette, self.colorPalette = colorizer(cpalette, MAINWINDOW.pal_path.text().rstrip())

        if self.blockPalette == False:
            QMessageBox.critical(MAINWINDOW, 'Error',
                                 "Palette not found, please check your path.")
            self.finished.emit()
            MAINWINDOW.pBar.setValue(0)
            self.mc.postToChat("Loading of the Point Cloud Interrupted")
            return None

        if self.blockPalette == None:
            QMessageBox.critical(MAINWINDOW, 'Error',
                                 "Palette format is incorrect.")
            self.finished.emit()
            MAINWINDOW.pBar.setValue(0)
            self.mc.postToChat("Loading of the Point Cloud Interrupted")
            return None



    def run(self):
        count = 0
        pcd = geometry.PointCloud()

        size = tuple_size(self.size)
        self.progress.emit(0)
        self.colorBase = 0

        with laspy.open(self.fname) as file:
            sub_bounds = recursive_split(
                file.header.x_min, file.header.y_min,
                file.header.x_max, file.header.y_max,
                size[0], size[1])

            self.mc.postToChat("Cloud2Craft successfully connect to the server")
            gcenter = np.array([(file.header.x_min + file.header.x_max) / 2,
                                    (file.header.y_min + file.header.y_max) / 2,
                                    (file.header.z_min + file.header.z_max) / 2])

            self.mc.postToChat("GRAVITY CENTER : X=" +
                               str(round(file.header.x_offset - (file.header.x_min + file.header.x_max / 2) + self.xoff)) + " Y=" +
                               str(round(file.header.y_offset - (file.header.y_min + file.header.y_max / 2) + self.zoff)) + " Z=" +
                               str(round(file.header.z_offset - (file.header.z_min + file.header.z_max / 2) + self.yoff))
                               )  # write ptc gravity center in Minecraft chat

            self.maxi.emit(int(file.header.point_count))

            if file.header.z_max > 256:
                self.mc.postToChat("Point cloud max height exceed max height of the world. Model will be cropped")

            try:
                timeStart = time()
                for points in file.chunk_iterator(self.pts_it):
                    if self.stop == True:
                        MAINWINDOW.acc_launch()
                        self.finished.emit()
                        MAINWINDOW.pBar.setValue(0)
                        self.mc.postToChat("Loading of the Point Cloud Interrupted")
                        return None
                    x, y = points.x.copy(), points.y.copy()
                    point_piped = 0

                    for i, (x_min, y_min, x_max, y_max) in enumerate(sub_bounds):
                        mask = (x >= x_min) & (x <= x_max) & (y >= y_min) & (y <= y_max)
                        if np.any(mask):
                            sub_points = points[mask]
                            pcd.points = utility.Vector3dVector(np.vstack((sub_points.x, sub_points.y,
                                                                           sub_points.z)).transpose())
                            if self.colorBase == 0 :
                                meanBlue = sum(sub_points.blue) / len(sub_points.blue)
                                meanRed = sum(sub_points.red) / len(sub_points.red)
                                meanGreen = sum(sub_points.green) / len(sub_points.green)
                                self.colorBase = 255 if (int(meanBlue) in range(-255, 255) and int(meanRed) in range(-255, 255) and int(meanGreen) in range(-255, 255)) else 65535
                            pcd.colors = utility.Vector3dVector(np.vstack((sub_points.red, sub_points.green,
                                                                           sub_points.blue)).transpose() / self.colorBase)  #256)
                            pcd.points = utility.Vector3dVector((pcd.points[:] - gcenter))

                            voxel_grid = geometry.VoxelGrid.create_from_point_cloud(pcd, voxel_size=self.vsize)
                            voxels = voxel_grid.get_voxels()
                            origin = voxel_grid.origin

                            for i in range(len(voxels)):
                                colorr = voxels[i].color
                                index = voxels[i].grid_index
                                color = closest_color(colorr, self.colorPalette)
                                self.mc.setBlock((index[1] + self.xoff + origin[1] / self.vsize),
                                                 (index[2] + self.zoff + origin[2] / self.vsize),
                                                 (index[0] + self.yoff + origin[0] / self.vsize),
                                                 *self.blockPalette[color])

                        point_piped += np.sum(mask)
                        if point_piped == len(points):
                            break

                    count += len(points)
                    self.progress.emit(count)

            except Exception as e:
                print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)

        # self.mc.postToChat("Cloud successfully inserted at " +
        #                    str(index[1] + self.xoff + origin[1] / self.vsize) + " " +
        #                    str(index[2] + self.zoff + origin[2] / self.vsize) + " " +
        #                    str(index[0] + self.yoff + origin[0] / self.vsize))

        MAINWINDOW.acc_launch()

        self.mc.postToChat("#==================#")
        self.mc.postToChat(" ")
        self.mc.postToChat("Finished, enjoy :)")
        self.mc.postToChat(" ")
        self.mc.postToChat("#==================#")
        print("Temps passé:", time() - timeStart)

        if MAINWINDOW.tp.isChecked():
            self.mc.player.setPos(self.xoff, 255, self.yoff)
        self.finished.emit()


class Main(QMainWindow):
    """
    Classe principale du programme
    """

    def __init__(self):
        """
        Initialisation

        Returns
        -------
        None.

        """
        super(Main, self).__init__()
        loadUi(parent_dir + "\mainwindow3.ui", self)
        self.setWindowTitle("Cloud2Craft")
        self.setWindowIcon(QIcon("./icon.ico"))
        self.init_ui()
        self.mc = None
        self.go = True

    def init_ui(self):
        """init User Interface"""
        self.update_vsize()
        self.Slider.valueChanged.connect(self.update_vsize)
        self.check_serv()
        read_param(self)
        self.positionBox.stateChanged.connect(self.updateOffsets)

    def updateOffsets(self):
        """Update the offsets box if insert on player position"""
        state = self.positionBox.isChecked()
        self.dx.setDisabled(state)
        self.dy.setDisabled(state)
        self.dz.setDisabled(state)

    def check_serv(self):
        """Check if the server is running or not and display on the main window"""
        self.mc = is_server_running()
        self.serv_stat.setStyleSheet("""background: black;
                                 font-weight: bold;
                                 color: """ +
                                     ("#63ae9d" if self.mc else "#f8606d"))
        self.serv_stat.setText((" 📡 Server Online" if self.mc else " ❌ Server Offline"))

    def update_vsize(self):
        self.vsize.setText(str(self.Slider.value()).rjust(4))

    def create_serv(self):
        """Create server on another thread to prevent the main interface from freezing"""
        self.serv_thread = QThread()
        self.serv_loader = init_serv()
        self.serv_loader.moveToThread(self.serv_thread)

        self.serv_thread.started.connect(self.serv_loader.run)

        self.serv_loader.finished.connect(self.on_gogogo_clicked)
        self.serv_loader.finished.connect(self.serv_thread.quit)
        self.serv_loader.finished.connect(self.serv_loader.deleteLater)
        self.serv_thread.finished.connect(self.serv_thread.deleteLater)

        self.serv_loader.error.connect(self.serv_error)

        self.serv_thread.start()

    def serv_error(self):
        """server error"""
        self.go = False
        self.acc_launch()
        self.serv_thread.quit()
        QMessageBox.critical(self, 'Error',
                             "Server failed to load. Please check your configuration.")
        # self.serv_thread.deleteLater()

    def load_cloud(self, fname, size, pts_it, vsize, xoff, yoff, zoff, pPos, cpalette):
        """
        Launch the thread for pcd loading

        Parameters
        ----------
        fname : TYPE STRING
            point cloud path.
        size : TYPE
            DESCRIPTION.
        pts_it : TYPE
            DESCRIPTION.
        vsize : TYPE INTEGER
            size of the voxels.
        xoff : TYPE INTEGER
            Offset on real X-AXIS.
        yoff : TYPE INTEGER
            Offset on real Y-AXIS.
        zoff : TYPE INTEGER
            Offset on real Z-AXIS.
        pPos : TYPE BOOLEAN
            True if insert on player, false if not.
        cpalette : TYPE INTEGER
            INDEX for the the palette choice.

        Returns
        -------
        None.

        """
        self.point_thread = QThread()
        self.point_loader = load_points(self.mc, fname, size, pts_it, vsize, xoff, yoff, zoff, pPos, cpalette)
        self.point_loader.moveToThread(self.point_thread)

        self.point_thread.started.connect(self.point_loader.run)
        # self.point_loader.finished(self.acc_launch)
        self.point_loader.finished.connect(self.point_thread.quit)
        self.point_loader.finished.connect(self.point_loader.deleteLater)
        self.point_thread.finished.connect(self.point_thread.deleteLater)

        self.point_loader.progress.connect(self.report)
        self.point_loader.maxi.connect(self.setmax)

        self.point_thread.start()

    def setmax(self, nummax):
        """set the maximum value for the progressBar"""
        self.pBar.setMaximum(nummax)

    def report(self, num):
        """set the progressBar value"""
        self.pBar.setValue(num)

    def acc_launch(self):
        """reset the launch btn"""
        self.gogogo.setText("Launch")
        self.gogogo.setEnabled(True)
        self.gogogo.setFlat(False)

    def inac_launch(self):
        """disable the launch btn"""
        self.gogogo.setText("...")
        self.gogogo.setDisabled(True)
        self.gogogo.setFlat(False)

    def stop_launch(self):
        """Set the style of the launch btn to stop"""
        self.gogogo.setText("Stop")
        self.gogogo.setEnabled(True)
        self.gogogo.setFlat(True)

    @pyqtSlot()
    def on_find_path_clicked(self):
        """
        Find the file path

        Returns
        -------
        None.

        """
        path = self.path.text().rstrip()
        fname = QFileDialog.getOpenFileName(self, 'Open a LIDAR file',
                                            "c://" if path == "" else path, "(*.laz; *las)")
        if fname[0] != "":
            self.path.setText(str(fname[0]))

    @pyqtSlot()
    def on_find_pal_clicked(self):
        """
        Find the custom palette path

        Returns
        -------
        None.

        """
        fname = QFileDialog.getOpenFileName(self, 'Open a custom palette',
                                            "c://", "(*.txt)")
        if fname[0] != "":
            self.pal_path.setText(str(fname[0]))

    @pyqtSlot()
    def on_adv_settings_clicked(self):
        """
        go from the main tab to the advanced settings

        Returns
        -------
        None.

        """
        self.stackedWidget_3.setCurrentIndex(1)

    @pyqtSlot()
    def on_find_serv_clicked(self):
        """
        Find the server path

        Returns
        -------
        None.

        """
        fname = QFileDialog.getOpenFileName(self, 'Select the server file',
                                            "c://", "(*.jar)")
        if fname[0] != "":
            self.ser_path.setText(str(fname[0]))

    @pyqtSlot()
    def on_apply_clicked(self):
        """
        apply the advanced settings

        Returns
        -------
        None.

        """
        self.stackedWidget_3.setCurrentIndex(0)
        save_param(self)
        create_bat(self)
        mod_serv_properties(self.ser_path.text().rstrip(), self.port.text().rstrip())

    @pyqtSlot()
    def on_cancel_clicked(self):
        """
        Go from the advanced settings to the main window
        """
        self.stackedWidget_3.setCurrentIndex(0)

    @pyqtSlot()
    def on_gogogo_clicked(self):
        """
        setup for loadding the pcd

        Returns
        -------
        None.

        """
        if self.gogogo.isFlat():
            self.point_loader.stop = True

        else:
            fname = ""
            try:
                fname = self.path.text()
                open(fname, "r").close()

            except IOError:
                QMessageBox.critical(self, 'Error',
                                     "Point cloud unreachable: the path is incorrect or the file is missing")

            if fname != "":
                self.inac_launch()
                self.mc = is_server_running()
                if not self.mc:
                    self.serv_stat.setStyleSheet("""background: black;
                                                 font-weight: bold;
                                                 color: #ffa36d""")
                    self.serv_stat.setText(" 🟠 Waiting for the server")
                    print("starting server...")
                    self.mc = self.create_serv()
                else:
                    self.serv_stat.setStyleSheet("""background: black;
                                                  font-weight: bold;
                                                  color: #63ae9d""")
                    self.serv_stat.setText(" 📡 Server Online")
                    self.go = True

                    if self.go:
                        vsize = self.Slider.value() / 1000
                        size = str(self.csizeh.value()) + "x" + str(self.csizev.value())
                        pts_it = self.ppi.value()
                        cpalette = self.pal.currentIndex()
                        playerPos = self.positionBox.isChecked()

                        xoff = self.dx.value()
                        yoff = self.dy.value()
                        zoff = self.dz.value()

                        self.stop_launch()

                        self.load_cloud(fname, size, pts_it, vsize, xoff, yoff, zoff, playerPos, cpalette)


parent_dir = str(os.path.dirname(os.path.realpath(__file__)))

APP = QApplication(sys.argv)

MAINWINDOW = Main()

MAINWINDOW.show()

sys.exit(APP.exec_())
