#!/usr/bin/python
#coding=utf-8
'''
import childDialog
reload(childDialog)
from childDialog import ChildWindow as ChildWindow
'''
import maya.cmds as mc
import maya.mel as mel
import os,glob,re
from threading import Thread
#import exportFbx
#reload(exportFbx)
#from exportFbx import exportBy
# N:\projectServer\SYYX\preproduction\capture\ep015\SYYX_ep015_cap\sc014\wuxi
try:
    from PySide2 import QtGui
    from PySide2 import QtCore
    from PySide2 import QtUiTools
    from PySide2.QtGui import *
    from PySide2 import QtWidgets
    from PySide2.QtCore import Signal
except ImportError:
    from PySide import QtGui
    from PySide import QtCore
    from PySide import QtUiTools
    from PySide.QtGui import *
    from PySide import QtWidgets

try:
	mel.eval("loadPlugin animImportExport;")
except RuntimeError:
	mc.confirmDialog(title="Error",button="Yes",icon="error",
	message="没有正常挂载Anim插件!") 

currentPath = r"E:/work_ref/transferAnim/transferAnim"
uiPath = os.path.join(currentPath, "transferAnim.ui")
#subUiPath = os.path.join(currentPath, "checkFiles.ui")
iconsPath = os.path.join(currentPath,"icons")
projPath = r"N:/projectServer"
#assetPaths = ["production","asset"]
shotPaths = ["preproduction","capture"]
#1功能错误。 2系统找不到指定的文件。3系统找不到指定的路径。4系统无法打开文件。 5拒绝访问 6句柄无效
errorIO = {"[Error 1]":"[功能错误]","[Error 2]":"[找不到文件]","[Error 3]":"[找不到路径]","[Error 4]":"[无法打开文件]","[Error 5]":"[拒绝访问]","[Error 6]":"[句柄无效]"}

class mainWin(QtWidgets.QDialog):
    main_Signal = Signal(list) #定义信号
    
    def __init__(self, uiPath, parent=None):
        super(mainWin, self).__init__(parent)
        self.uifile = uiPath
        self.loader = self.loadUi()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.loader)
        self.setLayout(layout)
        self.createContextMenu()
        self.setupConnect()
        #self.exportClass = exportBy()
        self.loadProj()
        self.loadRig()

    #:SIGNAL connect
    def setupConnect(self):
        self.loader.projectLW.itemClicked.connect(self.loadShot)
        self.loader.projectRefreshBTN.clicked.connect(self.loadProj)
        self.loader.shotRefreshBTN.clicked.connect(self.loadShot)
        self.loader.shotTW.clicked.connect(self.loadSubShot)
        self.loader.delShotBTN.clicked.connect(self.delShot)
        self.loader.openFolderBTN.clicked.connect(self.findShot)
        #self.loader.cmdloadBTN.clicked.connect(self.cmdloadUE4)
        #self.loader.loadBTN.clicked.connect(self.loadUE4Project)
        #self.loader.clearBTN.clicked.connect(self.clearFolder)
        #self.loader.importBTN.clicked.connect(self.importShot)
        self.setWindowTitle("Transfer Anim File ...")
        self.setGeometry(300,300,300,150)

    def getSubwininfo(self,subList):   # # 主窗口的槽函数
        self.childRecL = subList
        print(self.childRecL)
        self.loader.textEdit.setText('\n'.join(self.childRecL))
        if self.kind == 'asset':
            self.exportAssetFiles()
        elif self.kind == 'shot':
            self.exportShotFiles()

    def createContextMenu(self):
        #创建右键菜单 
        # 必须将ContextMenuPolicy设置为Qt.CustomContextMenu
        # 否则无法使用customContextMenuRequested信号
        for TW in [self.loader.fileTW  ,self.loader.shotTW]:
            TW.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.loader.shotTW.customContextMenuRequested.connect(self.showShotTWContextMenu)
        self.loader.fileTW.customContextMenuRequested.connect(self.showFileTWContextMenu)

        for TW in [self.loader.fileTW ,self.loader.shotTW]:
            # 创建QMenu
            TW.contextMenu = QtWidgets.QMenu(self)
            if TW.objectName() == "shotTW":
                self.loader.actionF1 = TW.contextMenu.addAction("导入")
                self.loader.actionC1 = TW.contextMenu.addAction("打开目录")
                self.loader.actionD1 = TW.contextMenu.addAction("删除文件")
                self.loader.actionE1 = TW.contextMenu.addAction("刷新")
                
                self.loader.actionC1.triggered.connect(self.findShot)
                self.loader.actionD1.triggered.connect(self.delShot)
                self.loader.actionE1.triggered.connect(self.loadShot)
                self.loader.actionF1.triggered.connect(self.importShot)
            if TW.objectName() == "fileTW":
                #self.loader.actionB2 = TW.contextMenu.addAction("导入maya")
                #self.loader.actionA2 = TW.contextMenu.addAction("创建目录")
                #self.loader.actionC2 = TW.contextMenu.addAction("打开目录")
                #self.loader.actionF2 = TW.contextMenu.addAction("目录改名")
                #self.loader.actionD2 = TW.contextMenu.addAction("删除文件")
                self.loader.actionE2 = TW.contextMenu.addAction("刷新")
                
                #self.loader.actionA2.triggered.connect(self.createFolder)
                #self.loader.actionB2.triggered.connect(self.actionHandler)
                #self.loader.actionC2.triggered.connect(self.findFile)
                #self.loader.actionD2.triggered.connect(self.delUE4File)
                #self.loader.actionF2.triggered.connect(self.renameFolder)
                self.loader.actionE2.triggered.connect(self.loadRig)
        return

    def showShotTWContextMenu(self, pos):
        #右键点击时调用的函数 

        # 菜单显示前，将它移动到鼠标点击的位置
        self.loader.shotTW.contextMenu.move(QtGui.QCursor().pos())
        self.loader.shotTW.contextMenu.show()

    def showFileTWContextMenu(self, pos):
        self.loader.fileTW.contextMenu.move(QtGui.QCursor().pos())
        self.loader.fileTW.contextMenu.show()

    def actionHandler(self):
        print("action handler")

    def inputDialog(self,cap):
        title, okPressed = QtWidgets.QInputDialog.getText(
            self.loader,
            '{0}'.format(cap),
            "输入框",
            QtWidgets.QLineEdit.Normal,
            "")
        
        if not okPressed:
            print(u'已经取消输入!')
            return None
        wrongRegex = re.compile('[^a-zA-Z0-9_]')
        if not wrongRegex.search(title)==None:
            mc.confirmDialog(title="Error",button="Yes",icon="error",
            message=u"只允许输入大小写字母、数字和下划线!")
            return None
        return title
        
    def showInput(self,onepath):
        #onepath= self.loader.fileTW.currentItem().text(1)
        if not os.path.isdir(onepath):
            return False
        oldpathL = os.listdir(onepath)
        result = self.inputDialog(u"请输入新的文件夹名称")
        if result==None:
            return False
        for oldpath in oldpathL:
            if result.lower() == oldpath.lower():
                mc.confirmDialog(title="Error",button="Yes",icon="error",
                message=u"存在同名的对象!")
                return False
        self.newFolderName = result
        return True

    def createFolder(self):
        onepath= self.loader.fileTW.currentItem().text(1)
        print("create handler")
        if self.showInput(onepath):
            newpath = os.path.join(onepath,self.newFolderName)
            os.system('{0} \"{1}\"'.format('mkdir',newpath))
            self._generate_item(self.loader.fileTW.currentItem(), self.newFolderName, newpath, 0)
        return
        
    def renameFolder(self):
        onepath= self.loader.fileTW.currentItem().text(1)
        print("rename handler")
        if self.showInput(onepath):
            newpath = os.path.join(onepath,self.newFolderName)
            os.system('{0} \"{1}\" {2}'.format('rename',onepath,self.newFolderName))
            self.loadUE4Files()
        return

    def loadUi(self):
        loader = QtUiTools.QUiLoader()
        strfile = QtCore.QFile(self.uifile)
        strfile.open(QtCore.QFile.ReadOnly)
        loadedUi = loader.load(strfile)
        strfile.close()
        return loadedUi

    def importShot(self):
        item = self.loader.shotTW.currentItem()
        if item is None:
            return
        mayafile = item.text(1)
        if os.path.isfile(mayafile):
            self.importMayaFile(mayafile)
        return

    def importMayaFile(self,mayafile):
        ext = mayafile.split(".")[-1].lower()
        if ext in ["mb","ma"]:
            self.exportClass.openMayaFile(mayafile=mayafile,ext=ext)
        elif ext == "fbx":
            self.exportClass.importFbxFile(xfile=mayafile)
        return

    def getAllShotFiles(self):
        files=[]
        self.childFiles = []
        item = self.loader.shotTW.currentItem()
        if os.path.isfile(item.text(1)):
            files=[item.text(1)]
        else:
            self._getchildItem(item)
            files.extend(self.childFiles)
        return files

    def _getchildItem(self, Item):
        count = Item.childCount()
        if count <1:
            return
        for i in range(count):
            child = Item.child(i)
            if os.path.isfile(child.text(1)):
                self.childFiles.append(child.text(1))
            else:
                self._getchildItem(child)
        return

    def loadRig(self):
        self.loader.fileTW.clear()
        conL = mc.ls('*:master_CON',type='transform' ,long=True)
        self.jointDict = {}
        for con in conL:
            self.jointDict[con] = self.loadConSub(con,{})
            if self.jointDict[con]!={}:
                item = QtWidgets.QTreeWidgetItem([con,con])
                item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DialogYesButton))
                self.loader.fileTW.addTopLevelItem(item)
                print('>>>Loading: {0}'.format(con))
                self.addJointItems(item,self.jointDict[con])
                #self.jointDict = {}
        return

    def addJointItems(self,item,jDict):
        for joint in jDict.keys():
            subitem = QtWidgets.QTreeWidgetItem([joint.split('|')[-1],joint])
            subitem.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DialogYesButton))
            item.addChild(subitem)
            self.addJointItems(subitem,jDict[joint])

    def loadConSub(self,con,subDict):
        #subDict={}
        objL = mc.listRelatives(con,children=True,f=True)
        if objL!=None:
            for obj in objL:
                if mc.nodeType(obj) in ['transform' ,'joint']:
                    subDict[obj]=self.loadConSub(obj,{})
        return subDict

    def delShot(self):
        TW = self.loader.shotTW
        self.delFileItem(TW)

    def delUE4File(self):
        TW = self.loader.fileTW
        self.delFileItem(TW)

    def delFileItem(self,TW):
        currNode = TW.currentItem()
        rootIndex = TW.indexOfTopLevelItem(currNode)
        ufile = currNode.text(1)
        isDeleted = self.delFile(ufile)
        if isDeleted:
            try:
                parentNode = currNode.parent()
                parentNode.removeChild(currNode)
            except Exception:
                try:
                    TW.takeTopLevelItem(rootIndex)
                except Exception:
                    print(Exception)

    def clearFolder(self):
        ufile = self.loader.fileTW.currentItem().text(1)
        if os.path.isdir(ufile):
            files = glob.glob(os.path.join(ufile,"*.*"))
            for fl in files:
                self.delFile(fl)
        self.loadUE4Files()
        return

    def findShot(self):
        ufile = self.loader.shotTW.currentItem().text(1)
        self.openFile(ufile)

    def findFile(self):
        ufile = self.loader.fileTW.currentItem().text(1)
        self.openFile(ufile)

    def delFile(self,ufile):
        if os.path.isfile(ufile):
            upath = os.path.realpath(os.path.dirname(ufile))
            basename = os.path.basename(ufile)
            try:
                os.system("del \"{0}\" /F".format(os.path.join(upath,basename)))
            except Exception as io:	
                info = self.replaceError(str(io))
                mc.confirmDialog(title="Error",button="Yes",icon="error",message="ERROR:{0}!".format(info))
                return False
        else:
            return False
        return True

    def replaceError(self,info):
        for key in errorIO.keys():
            if key in info:
                xstr = "{0}{1}".format(errorIO[key],info.split("]")[-1])
                return xstr

    def openFile(self,ufile):
        print(ufile)
        if os.path.isfile(ufile):
            upath = os.path.abspath(os.path.dirname(ufile))
            os.system("start explorer \"{0}\"".format(upath))
        elif os.path.isdir(ufile):
            upath = os.path.abspath(ufile)
            os.system("start explorer \"{0}\"".format(upath))
        return

    def loadProj(self):
        self.loader.projectLW.clear()
        if not os.path.isdir(projPath):
            mc.confirmDialog(title="Error",button="Yes",icon="error",
            message="需要一个正确的项目路径! {0}".format(projPath))
            return
        directoryL = os.listdir(projPath)
        #print(directoryL)
        self.projects = []
        for directory in directoryL:
            if os.path.isdir(os.path.join(projPath,directory)) and directory.isalpha():
                self.projects.append(directory)
                item = QtWidgets.QListWidgetItem(directory)
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                self.loader.projectLW.addItem(item)
                item = QtWidgets.QListWidgetItem(directory)
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
        return

    def foreachFile(self,formats,directory,item):
        self.loader.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.list_dir(item, directory,['fbx','uasset'])
        self.loader.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        return
 
    def list_dir(self, parent, directory,formats):
        for obj in os.listdir(directory):
            tmp_path = os.path.join(directory, obj)
            if os.path.isdir(tmp_path):
                dir_item = self._generate_item(parent, obj, tmp_path, 0)
                self.list_dir(dir_item, tmp_path,formats)
            elif os.path.isfile(tmp_path):
                if tmp_path.split('.')[-1] in formats:	
                    self._generate_item(parent, obj, tmp_path, 1)
 
    def _generate_item(self, parent, name, path, node_type):
        child =  QtWidgets.QTreeWidgetItem([name,path])
        if node_type ==0:
            child.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
        else:
            child.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon))
        parent.addChild(child)
        return child

    def _getShotTWRootItem(self, Item):
        if Item is None:
            currentItem = self.shotTW.currentItem()
            parentItem = currentItem.parent()
        else:
            currentItem = Item
            parentItem = currentItem.parent()
        # 如果不是ROOT节点，则继续
        if not parentItem is None:
            rootItem = self._getShotTWRootItem(parentItem)
        else:
            rootItem = currentItem
        return rootItem

    def collectAllFiles(self,formats,directory,deepin):
        # 光标改变
        self.loader.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        fileDict={}
        level=""
        for n in range(deepin):
            level+="/*"
        paths = glob.glob("{0}{1}/*".format(directory,level))
        for path in paths:
            pathL = path.replace("\\","/").split("/")
            if os.path.isdir(path):
                if deepin == 3:
                    if not pathL[-4] in fileDict.keys():
                        fileDict[pathL[-4]]={}
                    if not pathL[-3] in fileDict[pathL[-4]].keys():
                        fileDict[pathL[-4]][pathL[-3]]={}
                    if not pathL[-2] in fileDict[pathL[-4]][pathL[-3]]:
                        fileDict[pathL[-4]][pathL[-3]][pathL[-2]]={}
                    if not pathL[-1] in fileDict.keys():
                        fileDict[pathL[-4]][pathL[-3]][pathL[-2]][pathL[-1]]={}
                if deepin == 2:
                    if not pathL[-3] in fileDict.keys():
                        fileDict[pathL[-3]]={}
                    if not pathL[-2] in fileDict[pathL[-3]]:
                        fileDict[pathL[-3]][pathL[-2]]={}
                    if not pathL[-1] in fileDict.keys():
                        fileDict[pathL[-3]][pathL[-2]][pathL[-1]]={}
                if deepin == 1:
                    if not pathL[-2] in fileDict.keys():
                        fileDict[pathL[-2]]={}
                    if not pathL[-1] in fileDict.keys():
                        fileDict[pathL[-2]][pathL[-1]]={}
                if deepin == 0:
                    if not pathL[-1] in fileDict.keys():
                        fileDict[pathL[-1]]={}
            elif os.path.isfile(path):
                basename = os.path.basename(path)
                if basename.split(".")[-1].lower() in formats:
                    if deepin == 3:
                        if not pathL[-4] in fileDict.keys():
                            fileDict[pathL[-4]]={}
                        if not pathL[-3] in fileDict[pathL[-4]].keys():
                            fileDict[pathL[-4]][pathL[-3]]={}
                        if not pathL[-2] in fileDict[pathL[-4]][pathL[-3]]:
                            fileDict[pathL[-4]][pathL[-3]][pathL[-2]]={}
                        fileDict[pathL[-4]][pathL[-3]][pathL[-2]][basename]="<file>"
                    if deepin == 2:
                        if not pathL[-3] in fileDict.keys():
                            fileDict[pathL[-3]]={}
                        if not pathL[-2] in fileDict[pathL[-3]]:
                            fileDict[pathL[-3]][pathL[-2]]={}
                        fileDict[pathL[-3]][pathL[-2]][basename]="<file>"
                    if deepin == 1:
                        if not pathL[-2] in fileDict.keys():
                            fileDict[pathL[-2]]={}
                        fileDict[pathL[-2]][basename]="<file>"
                    if deepin == 0:
                        if not pathL[-1] in fileDict.keys():
                            fileDict[pathL[-1]]={}
                        fileDict[pathL[-1]][basename]="<file>"
        # 光标恢复
        self.loader.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        return fileDict

    def addChildren(self, ndict, item):
        orinname = item.text(1)
        #if isinstance (ndict,list):
        for n in ndict.keys():
            if isinstance(ndict[n], str): 
                child =  QtWidgets.QTreeWidgetItem([n,orinname+"/"+n])
                child.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon))
                item.addChild(child)
            else:
                child =  QtWidgets.QTreeWidgetItem([n,orinname+"/"+n])
                child.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                item.addChild(child)
                self.addChildren(ndict[n], child)
        return 

    def loadSubChildShot(self,x):
        count = self.loader.shotTW.currentItem().childCount()
        if count > 0:
            return
        onePath = self.loader.shotTW.currentItem().text(1)
        fileDict = self.collectAllFiles(["anim","orcen","fbx"],onePath,x)
        self.addChildren(fileDict, self.loader.shotTW.currentItem())
        self.loader.shotTW.setItemExpanded(self.loader.shotTW.currentItem(),True)
        return

    def loadSubShot(self):
        cItem = self.loader.shotTW.currentItem()
        cPath = cItem.text(1)
        cDir = cItem.text(0)
        #print(cPath,cDir)
        if os.path.isdir(cPath) and cDir[:2] == "ep":
            self.loadOneSeq('sc',cDir)
        elif os.path.isdir(cPath) and cDir[:2] == "sc":
            #self.loadOneSeq('sh',cDir)
            self.loadSubChildShot(1)
        elif os.path.isdir(cPath) and not cDir[:2] in ["ep", "sh"]:
            self.loadSubChildShot(1)
        return

    def loadOneSeq(self,head,cDir):
        epItem = self.loader.shotTW.currentItem()
        currentProject = self.loader.projectLW.selectedItems()[0].text()
        top = self.loader.shotTW.indexOfTopLevelItem(epItem)
        if top==-1 and head =='ep':
            return
        count = epItem.childCount()
        if count > 0:
            return
        #epPath = os.path.join(projPath,currentProject,"\\".join(shotPaths))
        epPath = epItem.text(1)
        #print(epItem,epPath)
        
        newPath = epPath
        if head=='sc':
            newPath = os.path.join(epPath,'{0}_{1}_{2}'.format(currentProject,cDir,'cap'))
        if not os.path.isdir(newPath):
            print(u"需要一个正确的镜头路径! {0}".format(newPath))
            #mc.confirmDialog(title="Error",button="Yes",icon="error",
            #message=u"需要一个正确的镜头路径! {0}".format(newPath))
            return
        directoryL = os.listdir(newPath)
        for directory in directoryL:
            if os.path.isdir(os.path.join(newPath,directory)) and directory[:2] == head:
                item = QtWidgets.QTreeWidgetItem([directory,os.path.join(newPath,directory)])
                #self.collectAllFiles("mb",os.path.join(kindPath,directory))
                item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                #self.addChildren(item, self.loader.shotTW.currentItem())
                epItem.addChild(item)
        self.loader.shotTW.setItemExpanded(epItem,True)
        return

    def loadShot(self):
        if self.loader.projectLW.selectedItems()==[]:
            return
        currentProject = self.loader.projectLW.selectedItems()[0].text()
        epPath = os.path.join(projPath,currentProject,"\\".join(shotPaths))
        self.loader.shotTW.clear()
        if not os.path.isdir(epPath):
            print(u"需要一个正确的镜头路径! {0}".format(epPath))
            #mc.confirmDialog(title="Error",button="Yes",icon="error",
            #message=u"需要一个正确的镜头路径! {0}".format(epPath))
            return
        self.episodes=[]
        directoryL = os.listdir(epPath)
        for directory in directoryL:
            if os.path.isdir(os.path.join(epPath,directory)) and directory[:2] == "ep":
                self.episodes.append(directory)
                item = QtWidgets.QTreeWidgetItem([directory,os.path.join(epPath,directory)])
                #self.collectAllFiles("mb",os.path.join(kindPath,directory))
                item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                self.loader.shotTW.addTopLevelItem(item)
        return

    def mainUI():
        dialog=mainWin(uiPath)
        dialog.show()

# --maya run scripts--
#import sys
#sys.path.append("E:/work_ref/transferAnim")
#import transferAnim
#reload(transferAnim)
#uiPath = transferAnim.uiPath
#tfdialog = transferAnim.main.mainWin(uiPath)
#tfdialog.show()
# end