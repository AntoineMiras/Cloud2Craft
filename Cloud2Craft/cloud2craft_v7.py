# -*- coding: utf-8 -*-

"""

 ██████╗██╗      ██████╗ ██╗   ██╗██████╗ ██████╗  ██████╗██████╗  █████╗ ███████╗████████╗
██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗╚════██╗██╔════╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝
██║     ██║     ██║   ██║██║   ██║██║  ██║ █████╔╝██║     ██████╔╝███████║█████╗     ██║
██║     ██║     ██║   ██║██║   ██║██║  ██║██╔═══╝ ██║     ██╔══██╗██╔══██║██╔══╝     ██║
╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝███████╗╚██████╗██║  ██║██║  ██║██║        ██║
 ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝        ╚═╝


                      -- By Antoine MIRAS and Baptiste BELLOCQ --


Cloud2Craft is under MIT License:

Copyright 2022 Antoine MIRAS and Baptiste BELLOCQ

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject
to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

"""

# =============================================================================
# Modules
# =============================================================================

import sys

import os

import subprocess

from time import sleep, time

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread

from PyQt5.uic import loadUi

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileDialog, QMessageBox)

from PyQt5.QtGui import QIcon

from open3d import geometry, utility

from mcpi.minecraft import Minecraft

import numpy as np

import laspy

# =============================================================================
# Custom Modules
# =============================================================================

from colorizer import colorizer

# =============================================================================
# Functions
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
    _r, _g, _b = rgb
    _r *= 256
    _g *= 256
    _b *= 256
    color_diffs = []

    for color in col_lst:
        _cr, _cg, _cb = color
        color_diff = np.sqrt((_r - _cr) ** 2 + (_g - _cg) ** 2 + (_b - _cb) ** 2)
        color_diffs.append((color_diff, color))
    return min(color_diffs)[1]


def save_param(instance):
    """Save the user preferences in a file"""
    txt = open(PARENT_DIRECTORY + "\\Ressources\\preferences.txt", "w+")
    txt.write("path-->" + instance.ser_path.text().rstrip().replace("\\", "/") + "\n" +
              "port-->" + instance.port.text().rstrip() + "\n" +
              "start-->" + str(instance.start.isChecked()) + "\n" +
              "tp-->" + str(instance.tp.isChecked()))
    txt.close()


def read_param(instance):
    """Retrieve the user preferences"""
    txt = open(PARENT_DIRECTORY + "\\Ressources\\preferences.txt", "r+")
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
    bat = open(path.replace(path.split("/")[-1], "launch_serv.bat"), "w+")
    bat.write('java -jar "' + path + '"')
    bat.close()


def mod_serv_properties(path, port):
    """Edit the server properties"""
    try:
        prop = open(path.replace(path.split(
            "/")[-1], "server.properties"), "r")
        lines = prop.readlines()
        prop.close()

        propp = open(path.replace(path.split(
            "/")[-1], "server.properties"), "w")
        for line in lines:
            if "server-port" not in line:
                propp.write(line)
            else:
                propp.write(line.split("=")[0] + "=" + port + "\n")
        propp.close()
    except Exception as _e:
        print(_e)
        QMessageBox.critical(
            MAINWINDOW, 'Error',
            "Server properties unreachable: the path is incorrect or the file is missing"
        )


def recursive_split(x_min, y_min, x_max, y_max, max_x_size, max_y_size):
    """
    Credits to the Laspy Documentation:
        https://laspy.readthedocs.io/en/latest/examples.html

    """
    x_size = x_max - x_min
    y_size = y_max - y_min

    if x_size > max_x_size:
        left = recursive_split(x_min, y_min, x_min +
                               (x_size // 2), y_max, max_x_size, max_y_size)
        right = recursive_split(x_min + (x_size // 2),
                                y_min, x_max, y_max, max_x_size, max_y_size)
        return left + right
    if y_size > max_y_size:
        _up = recursive_split(x_min, y_min, x_max, y_min +
                             (y_size // 2), max_x_size, max_y_size)
        _down = recursive_split(x_min, y_min + (y_size // 2),
                               x_max, y_max, max_x_size, max_y_size)
        return _up + _down
    return [(x_min, y_min, x_max, y_max)]


def is_server_running():
    """Check if the server is runing"""
    try:
        _mc = Minecraft.create(address="localhost", port=4711)
        return _mc
    except Exception as _e:
        print(_e)
        return False

# =============================================================================
# Ui / Thread
# =============================================================================


class InitServ(QObject):
    """
    Launch the server if not running
    """
    finished = pyqtSignal()
    error = pyqtSignal()

    def run(self):
        """
        run the server, return None
        """
        try:
            dirr = MAINWINDOW.ser_path.text()  # on recup le chemin du serv
            pipe = subprocess.Popen(dirr.replace(dirr.split("/")[-1], "") + "launch_serv.bat",
                                    cwd=dirr.replace(dirr.split("/")[-1], ""),
                                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                                    )  # on lance la commande pour créer un serveur

            while not MAINWINDOW._mc:  # tant que le serveur n'est pas lancé
                sleep(3)  # petite pause
                if pipe.poll() is None:
                    MAINWINDOW._mc = is_server_running()  # on regarde si il fonctionne
                else:
                    self.error.emit()
                    return None
            self.finished.emit()  # on dit que le thread est finito
            return None  # on retourne rien

        except Exception as _e:
            print(_e)
            self.error.emit()
            return None

class LoadPoints(QObject):
    """Load points class, permit to load on another thread"""
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    maxi = pyqtSignal(int)

    def __init__(self):
        super(LoadPoints, self).__init__()

        xoff = MAINWINDOW.dx.value()
        yoff = MAINWINDOW.dy.value()
        zoff = MAINWINDOW.dz.value()

        self._mc = MAINWINDOW._mc
        self.fname = MAINWINDOW.path.text()
        self.size = (MAINWINDOW.csizeh.value(), MAINWINDOW.csizev.value())
        self.pts_it = MAINWINDOW.ppi.value()
        self.vsize = MAINWINDOW.Slider.value() / 1000
        self.start = True
        if MAINWINDOW.positionBox.isChecked():
            try:
                xoff, zoff, yoff = self._mc.player.getPos()
            except Exception as e:
                QMessageBox.critical(MAINWINDOW, 'Error',
                                     "Player position couldn't be recovered, please retry.")
                print(e)
                self.finished.emit()
                self.start = False
                return

        self.xoff = xoff
        self.yoff = yoff
        self.zoff = zoff
        self.stop = False
        self.block_palette, self.color_palette = colorizer(MAINWINDOW.pal.currentIndex(),
                                                           MAINWINDOW.pal_path.text().rstrip())

        if not self.block_palette:
            QMessageBox.critical(MAINWINDOW, 'Error',
                                 "Palette not found, please check your path.")
            self.finished.emit()
            MAINWINDOW.pBar.setValue(0)
            self._mc.postToChat("Loading of the Point Cloud Interrupted")
            return

        if self.block_palette is None:
            QMessageBox.critical(MAINWINDOW, 'Error',
                                 "Palette format is incorrect.")
            self.finished.emit()
            MAINWINDOW.pBar.setValue(0)
            self._mc.postToChat("Loading of the Point Cloud Interrupted")
            return

    def run(self):
        """
        load the points
        inspired by the laspy documentation:
            https://laspy.readthedocs.io/en/latest/examples.html
        """
        if not self.start:
            MAINWINDOW.acc_launch()
            self.finished.emit()
            return

        count = 0
        pcd = geometry.PointCloud()

        size = self.size
        self.progress.emit(0)
        color_base = 0

        with laspy.open(self.fname) as file:
            sub_bounds = recursive_split(
                file.header.x_min, file.header.y_min,
                file.header.x_max, file.header.y_max,
                size[0], size[1])

            self._mc.postToChat(
                "Cloud2Craft successfully connect to the server!"
                )
            gcenter = np.array([(file.header.x_min + file.header.x_max) / 2,
                                (file.header.y_min + file.header.y_max) / 2,
                                (file.header.z_min + file.header.z_max) / 2])

            # write ptc gravity center in Minecraft chat
            self._mc.postToChat("GRAVITY CENTER : X=" +
                               str(round(self.xoff))
                               + " Y=" + str(round(self.zoff))
                               + " Z=" + str(round(self.yoff))
                               )

            self.maxi.emit(int(file.header.point_count))

            try:
                time_start = time()
                for points in file.chunk_iterator(self.pts_it):
                    if self.stop:
                        MAINWINDOW.acc_launch()
                        self.finished.emit()
                        MAINWINDOW.pBar.setValue(0)
                        self._mc.postToChat(
                            "Loading of the Point Cloud Interrupted")
                        return None
                    _x, _y = points.x.copy(), points.y.copy()
                    point_piped = 0

                    for i, (x_min, y_min, x_max, y_max) in enumerate(sub_bounds):
                        mask = (_x >= x_min) & (_x <= x_max) & (
                            _y >= y_min) & (_y <= y_max)
                        if np.any(mask):
                            sub_points = points[mask]

                            pcd.points = utility.Vector3dVector(
                                np.vstack((sub_points.x,
                                           sub_points.y,
                                           sub_points.z)
                                          ).transpose())

                            # Tricks to calculate the color base
                            # IE if the color needs to be divided by 255**2 or 255

                            if color_base == 0:
                                mean_blue = sum(sub_points.blue) / \
                                    len(sub_points.blue)
                                mean_red = sum(sub_points.red) / \
                                    len(sub_points.red)
                                mean_green = sum(sub_points.green) / \
                                    len(sub_points.green)
                                color_base = 255 if (
                                    int(mean_blue) in range(-255, 255) \
                                        and int(mean_red) in range(-255, 255) \
                                            and int(mean_green) in range(-255, 255)
                                            ) else 65535

                            pcd.colors = utility.Vector3dVector(np.vstack(
                                (sub_points.red,
                                 sub_points.green,
                                 sub_points.blue)).transpose() / color_base)

                            pcd.points = utility.Vector3dVector(
                                (pcd.points[:] - gcenter))

                            voxel_grid = geometry.VoxelGrid.create_from_point_cloud(
                                pcd, voxel_size=self.vsize)
                            voxels = voxel_grid.get_voxels()
                            origin = voxel_grid.origin

                            for i in range(len(voxels)):
                                colorr = voxels[i].color
                                index = voxels[i].grid_index
                                color = closest_color(
                                    colorr, self.color_palette)

                                # Insert Voxels, regarding the voxel size and the origin
                                self._mc.setBlock(
                                    (index[1] + self.xoff + origin[1] / self.vsize),
                                    (index[2] + self.zoff + origin[2] / self.vsize),
                                    (index[0] + self.yoff + origin[0] / self.vsize),
                                    *self.block_palette[color]
                                    )

                        point_piped += np.sum(mask)
                        if point_piped == len(points):
                            break

                    count += len(points)
                    self.progress.emit(count)

            except AttributeError as _e:
                print(_e)
                QMessageBox.critical(self, 'Error',
                                     "Error when reading the point cloud, please check console for further informations.")


            except Exception as _e:
                print(_e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(fname, "line", exc_tb.tb_lineno, exc_type, exc_obj)


        MAINWINDOW.acc_launch()

        # Small Report
        self._mc.postToChat(" ")
        self._mc.postToChat(" ")
        self._mc.postToChat("#==================================================#")
        self._mc.postToChat(" ")
        self._mc.postToChat(" ")
        self._mc.postToChat("Finished in " +
                            str(round(time() - time_start, 2)) +
                            " seconds, enjoy :)")
        self._mc.postToChat(" ")
        self._mc.postToChat("Cloud2Craft, by Antoine MIRAS and Baptiste BELLOCQ")
        self._mc.postToChat(" ")
        self._mc.postToChat(" ")
        self._mc.postToChat("#==================================================#")

        if MAINWINDOW.tp.isChecked():
            self._mc.player.setPos(self.xoff, 255, self.yoff)
        self.finished.emit()


class Main(QMainWindow):
    """
    Main class
    """

    def __init__(self):
        """
        Initialisation

        Returns
        -------
        None.

        """
        super(Main, self).__init__()
        loadUi(PARENT_DIRECTORY + "\\Ressources\\mainwindow.ui", self)
        self.setWindowTitle("Cloud2Craft")
        self.setWindowIcon(QIcon("./Ressources/icon.ico"))
        self.init_ui()
        self._mc = None
        self._go = True

    def init_ui(self):
        """init User Interface"""
        self.update_vsize()
        self.Slider.valueChanged.connect(self.update_vsize)
        self.check_serv()
        read_param(self)
        self.positionBox.stateChanged.connect(self.update_offsets)

    def update_offsets(self):
        """Update the offsets box if insert on player position"""
        state = self.positionBox.isChecked()
        self.dx.setDisabled(state)
        self.dy.setDisabled(state)
        self.dz.setDisabled(state)

    def check_serv(self):
        """Check if the server is running or not and display on the main window"""
        self._mc = is_server_running()
        self.serv_stat.setStyleSheet("""background: black;
                                 font-weight: bold;
                                 color: """ +
                                     ("#63ae9d" if self._mc else "#f8606d"))
        self.serv_stat.setText(
            (" 📡 Server Online" if self._mc else " ❌ Server Offline"))

    def update_vsize(self):
        "update size indicator when slider is moved"
        self.vsize.setText(str(self.Slider.value()).rjust(4))

    def create_serv(self):
        """Create server on another thread to prevent the main interface from freezing"""
        self.serv_thread = QThread()
        self.serv_loader = InitServ()
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
        self._go = False
        self.acc_launch()
        self.serv_thread.quit()
        QMessageBox.critical(self, 'Error',
                             "Server failed to load. Please check your configuration.")

    def load_cloud(self):
        """
        Launch the thread for pcd loading
        """
        self.point_thread = QThread()
        self.point_loader = LoadPoints()
        self.point_loader.moveToThread(self.point_thread)

        self.point_thread.started.connect(self.point_loader.run)

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
        mod_serv_properties(self.ser_path.text().rstrip(),
                            self.port.text().rstrip())

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
                QMessageBox.critical(
                    self, 'Error',
                    "Point cloud unreachable: the path is incorrect or the file is missing")

            if fname != "":
                self.inac_launch()
                self._mc = is_server_running()
                if not self._mc:
                    self.serv_stat.setStyleSheet("""background: black;
                                                 font-weight: bold;
                                                 color: #ffa36d""")
                    self.serv_stat.setText(" 🟠 Waiting for the server")
                    print("starting server...")
                    self.create_serv()

                else:
                    self.serv_stat.setStyleSheet("""background: black;
                                                  font-weight: bold;
                                                  color: #63ae9d""")
                    self.serv_stat.setText(" 📡 Server Online")
                    self._go = True

                    if self._go:
                        self.stop_launch()
                        self.load_cloud()


PARENT_DIRECTORY = str(os.path.dirname(os.path.realpath(__file__)))

APP = QApplication(sys.argv)

MAINWINDOW = Main()

MAINWINDOW.show()

sys.exit(APP.exec_())
