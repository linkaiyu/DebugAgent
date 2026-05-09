# summary:

this is the test engine that implements the feature of pytest that runs the test code without touching/changing the tested code, can run the test code as is.
It supports:
  1. running a specific function in a script,
  2. provide spec to capture data for a targeted function,
  3. detour IO functions,
  4. stage arguments, environment vars
  5. run a trace with trace configuration on a script (using trace_core.py in a dynamically crated stecustomize.py file so that a script can be bootstrapped with tracing)
  6. 

The goal is to have a container like environment that can virtualize things for test
This tool is designed to be AI Agent friendly so that the kill can instruct agent to use in the diagnose-fix-verify-fix loop

This tool can be used by test skill or prompt

Runner_Trace_Core.py: 
    Run_Script_Integrated( 
      script: Union[str, Path],
      args: Optional[Iterable[Union[str, int, float]]] = None,
      extra_env: Optional[Dict[[str, Union[str, int, float]]] = None,
      trace_config: Optional[Dict[str,, Any]]=None,
      log_name: Optional[str] = None,
      log_dir: Optional[Union[str, Path]] = None,
      max_log_bytes: int = DEFAULT_MAX_LOG_BYTES,
      stubs: Optional[Dict[str, object]] = None,
      run_name: Optional[str] = None,
      entrypoint: Optional[Callable[[Dict[str, object]], None]] = None,
      import_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
      injection: Optional[InjectionConfig] = None,
      ) -> RunArtifacts

      e.g.
      
      args = "["--test-mode"],
      extra_env={"ENV": "prd", "REGION": "us-east-1"]},
      log_name = None,
      log_dir= str(WORKSPACE_DIR),
      entrypoint=test_main


    def test_main(script_globals)
      def _detoured_function(data)
          print(f"detoured function {data}")

    args = sys.argv[1:]

    testClass = script_globals["TestClass"]()  #get the class and init instance
    testClass.method_two = _detoured_function

    testClass.method_one()  # method_one() calls method_two() which get detoured by _detoured_function()

    Run_Script_Integrated(
      script = "myscript.py",
      args = "["--test-mode"],
      extra_env={"ENV": "prd", "REGION": "us-east-1"]},
      log_name = None,
      log_dir= str(WORKSPACE_DIR),
      entrypoint=test_main
=======================
  # capture data
  to run the existing script and capture the targeted function parameters, save the output to a file to be used as test data.
  spec keys: script, capture_targets (list of dot-paths0

  run_capture_from_spec( 
    spec: Union[str, Path, Dict[str, Any]],
    output_dir: Optional[Union[str, Path]] = None,
    ) -> RunResult

  # run_from_spec
  takes a single spec dict (or path to a json file) containing all run parameters, returns a structured RunResult and writes run_result.json.

  Spec keys:
    - script 9str, required): path to py script
    - args
    -env
    - import_overrides
    - recoder_targets (dot-paths in script globals to replace with EventRecoder.wrap() stub. Each entry becomes an event source that the assertion DSL can query.
    - assertions
    - trace_config
    - run_name
    - log_name
    - log_dir

    
