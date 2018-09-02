#this is the base class for tester objects
import sys
import subprocess
import logging
import os
from time import clock
from result import Result

studentLogger = logging.getLogger('errorLogger.progressLogger.studentLogger')
studentLogger.setLevel(logging.INFO)
h = logging.StreamHandler()
h.setLevel(logging.INFO)
studentLogger.addHandler(h)

class Tester(object):
  """
  Tester
  abstract class representing a testing interface
  """
  __name__ = 'Tester' #the name of this class

  INPUT_STDIN = 1 #input is expected to come via standard input
  INPUT_CMDLINE = 2 #input is expected to comve via the command line
  OUTPUT_STDOUT = 3 #output of executable will be to the standard output
  OUTPUT_FILE = 4  #exectuables output will be a file

  _PROGRAM_COMPLETED = 5 #the program completed the test
  _PROGRAM_CRASHED = 6 #the program crashed during a test
  _PROGRAM_TIMED_OUT = 7 #the program timed out during a test

  def str2InputType(typename):
    """converts the string name of the input type to the internal type
    @typename: the name of the type. either
      stdin
      cmdline
    """
    if(typename.lower() == 'stdin'):
      return Tester.INPUT_STDIN
    elif(typename.lower() == 'cmdline'):
      return Tester.INPUT_CMDLINE
    else:
      raise ValueError('Unknown input type ' + typename)

  def str2OutputType(typename):
    """converts the string name of the output type to the internal type
    @typename: the name of the type. either
      stdout
      file
    """
    if(typename.lower() == 'stdout'):
      return Tester.OUTPUT_STDOUT
    elif(typename.lower() == 'file'):
      return Tester.OUTPUT_FILE
    else:
      raise ValueError('Unknown input type ' + typename)
    
  
  def __init__(self, executable,
               usingCmdArgs, usingStdin, outputType,
               inDir, solDir, scratchDir,
               maxRunTime = 5, cmdArgs = None, lines2skip = 0):
    """
    @executable: the name of the exectuable to be run
    @usingCmdArgs: Are command line arguments being used?
    @usingStdin: Will there be input from the standard input?
    @outputType: how are outputs generated: Either
      OUTPUT_STDOUT: for when the solution is sent to standard out or
      OUTPUT_FILE: for when the solution is sent to a file
    @inDir: the name of the directory containing the inputs to be used for testing
      the naming convention for the tests contained within is testname-test.filetype
    @solDir: the name of the directory containing the solutions
      the naming convention for the solutions contained within is testname-sol.filetype
    @scratchDir: directory to write scratch files in
    @maxRunTime: the maximum number of seconds to run the program or
      None to allow the program to run until completion (if it does not terminate the program will hang)
    @cmdArgs: a list of additional command line arguments to the executable
    @lines2skip: number of lines of output program and solution file to skip
    """
    self.executable = executable
    self.usingCmdArgs = usingCmdArgs
    self.usingStdin = usingStdin
    self.outputType = outputType
    self.inDir = inDir
    self.solDir = solDir
    self.scratchDir = scratchDir
    self.maxRunTime = maxRunTime
    self.lines2skip = lines2skip
    if cmdArgs == None:
      self.cmdArgs = []
    else:
      self.cmdArgs = cmdArgs.copy()

    self.testFiles = [self.inDir + os.sep +
                      test for test in os.listdir(inDir) if not test.startswith('.')] #get the tests in the test directory
    self.testFiles.sort() #make the tests sorted

    if(scratchDir == None):
      self.userOut = None
    else:
      self.userOut = scratchDir + os.sep + 'userOut.txt' #file to temporarily store the use's output
    
    self.startTime = 0 #when did the test begin running
    self.endTime = 0   #when did the test end running
    
    self.results = [] #the results of the testing

  def _runOne(self, inFileName, outFileName = None):
    """run self.executable using the inputs contained in inFileName
       @inFileName: the name of the file containing the inputs
       @outFileName: the name of the file to write the program's stdout to if the solution is contained in the stdout
       @returns: the success status of running the program
       """
    #determine how to pass input file
    infile = None #the input file to be used
    additionalArgs = []
    with open(inFileName) as infile:
      if(self.usingCmdArgs): #using command line arguments
        num_args = int(infile.readline()) #the first line contains the number of command line arguments
        for i in range(num_args): #read the command arguments in
          additionalArgs.append(infile.readline().strip())
      #remaining lines in the file are considerd input to be given
      #via standard input
  
      #determine how outputs will be generated
      outfile = None
      if(self.outputType == Tester.OUTPUT_STDOUT): #outputting to stdout
        outfile = open(outFileName,'w') #open a file to hold the results
      elif(self.outputType == Tester.OUTPUT_FILE): #outputting to a file
        raise NotImplementedError #nothing we can really do as of now
      else:
        raise NotImplementedError

      #this clears out python's buffer so that the program run through subprocess
      #actually gets input. Another fix if this stops working is to open the file in unbuffered mode
      #http://stackoverflow.com/questions/22417010/subprocess-popen-stdin-read-file
      infile.seek(infile.tell()) 
      
      studentLogger.info('Preparing to test %s on %s', self.executable, os.path.basename(inFileName))

      #start the clocks
      self.endTime = clock()
      self.startTime = clock()

      #run the program
      with subprocess.Popen([self.executable] + self.cmdArgs + additionalArgs,
                            stdin = infile,
                            stdout = outfile,
                            stderr = subprocess.PIPE,
                            universal_newlines = True) as program:
        try:
          program.wait(timeout = self.maxRunTime) #wait for the program to finish
          self.endTime = clock() #program completed
          err = '\t'.join(program.stderr.readlines()) #always have to read the pipes
          if(program.returncode != 0):
            studentLogger.warning('%s %s crashed for the following reasons:\n\t%s\n',
                                  self.executable, ' '.join(self.cmdArgs), err)
            return Tester._PROGRAM_CRASHED
          else:
            return Tester._PROGRAM_COMPLETED
            
        except subprocess.TimeoutExpired:
          studentLogger.warning('%s %s timed out', ' '.join(self.cmdArgs), self.executable)
          program.kill()
          return Tester._PROGRAM_TIMED_OUT
          
      
  #end _runOne

  def testOne(self, inFile, solFile):
    """
    run the executable using inFile as the inputs
    and checking the output against solFile
    @inFile: the name of the file containing the inputs
    @solFile: the name of the file containg the solution
    @returns: a Result
    """
    progStatus = self._runOne(inFile, self.userOut)#run the program
    testName = os.path.basename(inFile) #the name of the test
    if(progStatus == Tester._PROGRAM_CRASHED):
      return Result(testName, False, 'Crashed')
    elif(progStatus == Tester._PROGRAM_TIMED_OUT):
      return Result(testName, False, 'Timed Out')
    else: #program completed successfully
      if(self.outputType == Tester.OUTPUT_STDOUT):
        with open(self.userOut) as answer:
          (correct, out, sol) = self._checkSolution(answer, solFile)
          if(correct):
            studentLogger.info('%s %s passed test %s',
                             self.executable, ' '.join(self.cmdArgs),
                             os.path.basename(inFile))
          else:
            first_diff = ''
            i = 0
            for (i,(o,s)) in enumerate(zip(out,sol)):
              if o != s:
                first_diff = 'First mismatch at word %d\nout = %s but sol = %s' % (i,o,s)
                #print(first_diff)
                break
            studentLogger.info('%s %s failed test %s. Program output: %s \n Solution: %s \n%s\n\n',
                             self.executable, ' '.join(self.cmdArgs),
                             os.path.basename(inFile), out, sol, first_diff)
          return Result(testName, correct, self.endTime - self.startTime )
      else: #haven't done anything where solutions are contained in files
        raise NotImplementedError
  #end testOne

  

  def generateSolutions(self):
    """generates all the solutions"""
    for test in self.testFiles:
      outfileName = test.replace('-test', '-sol')
      outfileName = self.solDir + os.sep + os.path.basename(outfileName)
      self._runOne(test,outfileName)
  #end generateSolutions

  def testAll(self):
    """
    Test all the tests
    @returns: a list of triples of the form (testName, correct, time taken)
    correct is True if the answer is correct and False if it is wrong
    time taken is expressed in seconds.

    See Result
    """

    self.results = [] #clear old results if any exist
    for test in self.testFiles:
      #get the name of the file containing the solution to this test
      sol = test.replace('-test', '-sol') #replace test with sol
      sol = self.solDir + os.sep + os.path.basename(sol) #prepend solution directory name and remove test directory path
      self.results.append(self.testOne(test, sol))
    try:
      os.remove(self.userOut)
    except FileNotFoundError:
      pass
  #end testAll

  def getResults(self):
    """get the results of the testing"""
    return self.results.copy()
  #end getResults
  
  def getNumTests(self):
    """get the number of tests that are to be preformed"""
    return len(self.testFiles)
  #end getNumTests

  def getNumCorrect(self):
    """
    get the number of answers that were correct
    should only be called after testAll is run
    @returns: the number of tests that were correct
    """
    numCorrect = 0
    for res in self.results:
      if(res.correct == True):
        numCorrect += 1
    return numCorrect
  #end getNumCorrect

  def getPercentCorrect(self):
    """get the precentage of right answers
    should only be called after testAll is run
    @returns: the percentage of tests that were correct
    """
    numCorrect = self.getNumCorrect()
    numTests = float(self.getNumTests())
    return numCorrect / numTests
  #end getPercentCorrect

  def getMissedTests(self):
    """
    get a list of the test names that were missed
    should only be called after testAll is run
    @returns: a list of the test names that were missed
    """
    return [res.testName for res in self.results if not res.correct]
  #end getMissedTests
  
  def getPassedTests(self):
    """
    get a list of the test names that were passed correctly
    should only be called after testAll is run
    @returns: a list of the test names that were passed correctly
    """
    return [res.testName for res in self.results if res.correct]
  #getPassedTests

  def getTestNames(self):
    """
    get the names of the tests to be run
    can be called before testAll is run
    @returns: a list containg the test names
    """
    return [test.rsplit(os.sep, 1)[-1] for test in self.testFiles]

  def _checkSolution(self, progOut, solutionFileName):
    """
    checkSolution
    @progOut: the opened file containing the student's answer
    @solutionFileName: the name of the file containg the solution
    @returns a tuple containing
    (correct, program out, solution)
    """
    
    progOut.flush() #make sure the file is up to date
    progOut.seek(0) #go back to the begining of the file
  
    try:
      sol = []
      with open(solutionFileName, 'r') as solFil: #open the solution file
        for (_1,_2,_3) in zip(range(self.lines2skip), progOut, solFil): #somehow placin zip as the first argument fixes a bug
          pass #skip the leading lines of input
          
        sol = [] #the solution
        for line in solFil: #make it so that white space does not matter
          sol += line.strip().split()
          
        out = [] # the programs output
        for line in progOut: #make it so that white space will not be an issue
          out += line.strip().split()
          
        if(out != sol):#output does not match solution
          return (False, out, sol)
         
      return (True, out, sol) #if everything is correct and all lines in the solution file are used the student got it right
    except UnicodeDecodeError:
      return (False, 'NonUnicode Character. This means your print statement is printing something crazy.', sol)
  # end _checkSolution

#end class Tester

if __name__ =='__main__':
  python = sys.executable
  t = Tester('./matmult.out', True, False, Tester.OUTPUT_STDOUT, 
              'Tests/tfiles', 'Solutions', '.')
  t.testAll()
  for res in t.getResults():
    print(res)
