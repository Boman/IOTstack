import os
import traceback

import ruamel.yaml
from deps.consts import templatesDirectory, buildCache, envFile, dockerPathOutput, composeOverrideFile
from deps.yaml_merge import mergeYaml

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True

buildScriptFile = 'build.py'

def buildServices(dockerComposeServicesYaml):
  try:
    runPrebuildHook()
    dockerFileYaml = {}
    menuStateFileYaml = {}
    dockerFileYaml["version"] = "3.6"
    dockerFileYaml["services"] = {}
    menuStateFileYaml["services"] = {}
    dockerFileYaml["services"] = dockerComposeServicesYaml
    menuStateFileYaml["services"] = dockerComposeServicesYaml

    if os.path.exists(envFile):
      with open(r'%s' % envFile) as fileEnv:
        envSettings = yaml.load(fileEnv)
      mergedYaml = mergeYaml(envSettings, dockerFileYaml)
      dockerFileYaml = mergedYaml

    if os.path.exists(composeOverrideFile):
      with open(r'%s' % composeOverrideFile) as fileOverride:
        yamlOverride = yaml.load(fileOverride)

      mergedYaml = mergeYaml(yamlOverride, dockerFileYaml)
      dockerFileYaml = mergedYaml

    with open(r'%s' % dockerPathOutput, 'w') as outputFile:
      yaml.dump(dockerFileYaml, outputFile, explicit_start=True, default_style='"')

    with open(r'%s' % buildCache, 'w') as outputFile:
      yaml.dump(menuStateFileYaml, outputFile, explicit_start=True, default_style='"')
    runPostBuildHook()
    return True
  except Exception:
    print("Issue running build:")
    traceback.print_exc()
    input("Press Enter to continue...")
    return False

def runPrebuildHook(dockerComposeServicesYaml):
  for (index, checkedMenuItem) in enumerate(checkedMenuItems):
    buildScriptPath = templatesDirectory + '/' + checkedMenuItem + '/' + buildScriptFile
    if os.path.exists(buildScriptPath):
        with open(buildScriptPath, "rb") as pythonDynamicImportFile:
          code = compile(pythonDynamicImportFile.read(), buildScriptPath, "exec")
        execGlobals = {
          "dockerComposeServicesYaml": dockerComposeServicesYaml,
          "toRun": "checkForPreBuildHook",
          "currentServiceName": checkedMenuItem
        }
        execLocals = locals()
        try:
          exec(code, execGlobals, execLocals)
          if "preBuildHook" in execGlobals["buildHooks"] and execGlobals["buildHooks"]["preBuildHook"]:
            execGlobals = {
              "dockerComposeServicesYaml": dockerComposeServicesYaml,
              "toRun": "preBuild",
              "currentServiceName": checkedMenuItem
            }
            execLocals = locals()
            exec(code, execGlobals, execLocals)
        except Exception:
          print("Error running PreBuildHook on '%s'" % checkedMenuItem)
          traceback.print_exc()
          input("Press Enter to continue...")
          try: # If the prebuild hook modified the docker-compose object, pull it from the script back to here.
            dockerComposeServicesYaml = execGlobals["dockerComposeServicesYaml"]
          except:
            pass

def runPostBuildHook():
  for (index, checkedMenuItem) in enumerate(checkedMenuItems):
    buildScriptPath = templatesDirectory + '/' + checkedMenuItem + '/' + buildScriptFile
    if os.path.exists(buildScriptPath):
        with open(buildScriptPath, "rb") as pythonDynamicImportFile:
          code = compile(pythonDynamicImportFile.read(), buildScriptPath, "exec")
        execGlobals = {
          "dockerComposeServicesYaml": dockerComposeServicesYaml,
          "toRun": "checkForPostBuildHook",
          "currentServiceName": checkedMenuItem
        }
        execLocals = locals()
        try:
          exec(code, execGlobals, execLocals)
          if "postBuildHook" in execGlobals["buildHooks"] and execGlobals["buildHooks"]["postBuildHook"]:
            execGlobals = {
              "dockerComposeServicesYaml": dockerComposeServicesYaml,
              "toRun": "postBuild",
              "currentServiceName": checkedMenuItem
            }
            execLocals = locals()
            exec(code, execGlobals, execLocals)
        except Exception:
          print("Error running PostBuildHook on '%s'" % checkedMenuItem)
          traceback.print_exc()
          input("Press Enter to continue...")
