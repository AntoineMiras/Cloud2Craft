<h1 align="center">
  <br>
  <picture>
    <img src="https://github.com/AntoineMiras/Cloud2Craft/blob/main/Cloud2Craft/Ressources/icon.ico" alt="Cloud2Craft" width="300"></a>
  </picture>
  <br>
  Cloud2Craft
  <br>
</h1>

<h4 align="center">A point clouds <a href="https://www.minecraft.net/" target="_blank">Minecraft</a> uploader</h4>

<div align="center">
  
  <a href="https://choosealicense.com/licenses/mit/">![MIT License](https://img.shields.io/badge/License-MIT-green.svg)</a>
  <a href="https://www.python.org/">![Python](https://img.shields.io/badge/Language-%F0%9F%90%8D%20Python-blue)</a>
  <a href="#">![Version](https://img.shields.io/badge/Version-1.0-orange)</a>
</div>
<p align="center">
    <a href="#overview">Overview</a> •
    <a href="#settings">Settings</a> •
    <a href="https://github.com/AntoineMiras/Cloud2Craft/releases/tag/Release">Download</a> •
    <a href="#authors">Authors</a> •
    <a href="#license">License</a>
</p>

<picture><img src="https://github.com/AntoineMiras/Cloud2Craft/blob/main/Cloud2Craft/Ressources/Banner.jpg"></picture>

## Overview

### What is Cloud2Craft?

Cloud2Craft is an open-source project, created by Antoine MIRAS and Baptiste BELLOCQ, that allow anyone to load massives point clouds into minecraft. The point clouds are commonly obtained using LiDAR technology or photogrammetry.
The goal of cloud2Craft is to allow anyone to import point clouds into the game, without the need for programming knowledge. Cloud2Craft is for everyone, but especially for those interested in point clouds, surveyors and virtual tour creators! 

## Install

1. Install all the requirements

```
pip install -r requirements.txt
```

2. Download server files 

Please download the files for the same version. The latest versions of Minecraft may have some compatibility issues — so in this tutorial we will work with minecraft 1.14.
links : 
- <a href="https://www.minecraft.net/en-us/download/server" target="_blank">Minecraft server</a>
- <a href="https://getbukkit.org/download/spigot" target="_blank">Spigot</a>
- <a href="https://dev.bukkit.org/projects/raspberryjuice?__cf_chl_tk=NTLm9y9wEYzpg27Ztui331kjzS.Ht8_lO5YcWxEwiCE-1674986542-0-gaNycGzNCSU" target="_blank">RaspberryJuice</a>

3. Make a new folder (minecraft-server) and move the .jar files downloaded in step 4.
4. In this folder, create a text file named eula.txt with the following line 
```
eula=True
```
5. Copy the path of the folder, we will use it in the next step.

You should have a file like this one :

<picture><img align="middle" src="https://github.com/AntoineMiras/Cloud2Craft/blob/main/Screenshots/server_directory_content.png" ></picture>

6. launch server :
```
cd path_of_your_files
java -jar spigot-1.14.3.jar
```
7. Move the RaspberryJuice .jar file into the plugins directory that spigot has created

8. Restart spigot with the same command as before :
```
java -jar spigot-1.14.3.jar
```
## Settings

### Input data

Cloud2Craft only accepts .las and .laz formats. This data can be obtained from photogrammetry software such as  <a href="https://alicevision.org/" target="_blank">Meshroom</a> or from Lidar acquisitions. 

### Voxel size 

Cloud2Craft allows you to choose the correspondence between a block in Minecraft and reality (voxel size). For example, a voxel size of 500 mm means that a block in Minecraft is 50 cm in reality. The smaller the voxel size, the more voxels you will have and the longer the processing time. Go slowly, a too small size can kick you off the server. 

### Color palette 

Several colour palettes are available : <br>
 <br>
  • Complete : a palette for good colour reproduction   <br>
  • Wool  <br>
  • Terracota   <br>
  • Custom 

### To player's position

Generates the centroid of the point cloud box at the player's position.

### Offsets

Apply the desired translations to the point cloud. Beware, minecraft follows an unconventional orthonormal reference frame. Here the Z represents the altitude (so the Y of Minecraft).

### Chunk size 

Cloud2Craft reads and generates the point cloud per chunk. These chunks are not Minecraft chunks, but represent the read/generated tiles of the las.laz format. 50x50 are suitable values.

<h1 align="center">


  <picture>
    <img src="https://github.com/AntoineMiras/Cloud2Craft/blob/main/Cloud2Craft/Ressources/menu.png" alt="menu" width="600"></a>
  </picture>

</h1>

## Screenshots

<picture><img src="https://github.com/AntoineMiras/Cloud2Craft/blob/main/Cloud2Craft/Ressources/background.png"></picture>
<p align="center">
  Laman Mahkota Bukit Serene Malaysia, credits to 
  <a href="https://geoslam.com/sample-data/"> GeoSlam </a>
</p>

<br>

<picture><img src="https://github.com/AntoineMiras/Cloud2Craft/blob/main/Screenshots/Mural.png"></picture>
<p align="center">
  Mural, 10 mm/block, credits to 
  <a href="https://betterprogramming.pub/from-point-clouds-to-minecraft-a-python-tutorial-1b14a87f3f0b"> Baptiste Bellocq </a>
</p>

<br>

## Authors

- [@AntoineMiras](https://github.com/AntoineMiras)
- [@bbellocq](https://github.com/bbellocq)

