import subprocess
import sys
import os
import shutil

# Check if it is a clean or a build
args = sys.argv
mode = None
if len(args) == 1 or args[1] == 'build':
  mode = 'build'
elif args[1] == 'clean':
  mode = 'clean'
else:
  sys.exit('Invalid param: ' + args[1])

def execCmd (cmd, silentFail):
  '''Executes the cmd and fails silently if asked to'''
  if silentFail:
    with open(os.devnull, 'w') as devnull:
      subprocess.call(cmd, shell=True, stderr=devnull)
  else:
    try:
      subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError, e:
      print 'Error message: '
      print e.output
      sys.exit('\nBuild stopped due to above error.')

def copyFilesToBuild (files, silentFail):
  '''Copies a list of files to build/'''
  for aFile in files:
    print 'copying ' + aFile + ' to build/' + aFile + '...'
    shutil.copy(aFile, 'build')

def copyDirectoriesToBuild (dirs, silentFail):
  '''Copies a list of directories to build/'''
  for aDir in dirs:
    print 'copying ' + aDir + ' to build/' + aDir + '...'
    shutil.copytree(aDir, 'build/' + aDir)

def moveToBuild (files, silentFail):
  '''Moves a list of files to build/'''
  for aFile in files:
    print 'moving ' + aFile + ' to build/' + aFile + '...'
    shutil.move(aFile, 'build/' + aFile)

def removeFiles (files, silentFail):
  '''Removes a list of files from pwd'''
  for aFile in files:
    print 'removing ' + aFile + '...'
    try:
      os.remove(aFile)
    except:
      if silentFail is False:
        raise;

def removeDirectories (dirs, silentFail):
  '''Removes a list of files from pwd'''
  for aDir in dirs:
    print 'removing ' + aDir + '...'
    shutil.rmtree(aDir)

def closureCompile (srcs, dest):
  '''Compiles each file in `srcs` and puts results as `dest`'''
  for aSrc in srcs:
    print 'Compiling ' + aSrc + ' to ' + dest + '/' + aSrc + '...'
    execCmd('java -jar closureCompiler/compiler.jar ' +
      '--language_in=ECMASCRIPT5 --js ' +
      aSrc + ' --js_output_file ' + dest + '/' + aSrc, silentFail=False)

def createDirectoryStructure ():
  print 'Creating directory structure...'
  os.mkdir('build')
  os.mkdir('build/bower_components')
  os.mkdir('build/bower_components/platform')
  os.mkdir('build/bower_components/polymer')

  # core-splitter needs an svg resource. vulcanize doesn't put resources in concatenated
  # file. So we must manually copy that build/ .
  os.mkdir('build/bower_components/core-splitter')


print 'Cleaning project...\n'
removeFiles(['panel.js', 'panel.html'], silentFail=True)
removeDirectories(['build'], silentFail=True)
print 'Project cleaned.\n'

if mode == 'clean':
  sys.exit('Run `python build.py` to build again.')

# TODO: Executing `bower` gives us:
# 'warning: possible EventEmitter memory leak detected. 11 listeners added.'
# So right now, we ask the user to do it manually. Must fix this.
'''print 'Getting dependencies with `bower`...'

execCmd('bower install', silentFail=False)'''

print 'Building project...\n'

createDirectoryStructure()

print 'Vulcanizing...\n'
execCmd('vulcanize --csp -o panel.html panel-orig.html', silentFail=False)

print 'Finished vulcanizing'

# Vulcanize shouldn't be asked to output result in build/ because it would then
# rewrite relative paths in files which we don't want. We'll anyway move everything
# to build/
# So we manually move panel.html after vulcanizing
moveToBuild(['panel.html'], silentFail=False)

print 'Compiling with Closure...\n'

closureCompile(srcs=[
  'panel.js',
  'panel-orig.js',
  'panel.js',
  'hostPageHelpers.js',
  'evalHelper.js',
  'DOMJSONizer.js',
  'devtools.js',
  'contentScript.js',
  'background.js',
  'perfContentScript.js',
], dest='build')

print 'Finished compiling'

print 'Adding files to build/ ...\n'

# All custom elements defined in the project need not be vulcanized since they are
# CSP compliant. All we need to do is copy them over to build/.
copyDirectoriesToBuild(['elements'], silentFail=False)

# panel.js is a product of vulcanize. Since it got compiled to build/ we don't need it.
removeFiles(['panel.js'], silentFail=False)

copyFilesToBuild(['devtools.html', 'manifest.json'], silentFail=False)

# <script>s are not copied by vulcanize, so these have to be moved in as well.
execCmd('cp bower_components/platform/platform.js build/bower_components/platform/platform.js',
  silentFail=False)
execCmd('cp bower_components/polymer/polymer.js build/bower_components/polymer/polymer.js',
  silentFail=False)
# core-splitter needs an svg resource.
execCmd('cp bower_components/core-splitter/handle.svg build/bower_components/core-splitter/handle.svg',
  silentFail=False)

print 'All done! The extension was built in `build`.\n'
