
/*
int** mat_add(int** A, int **B, int num_rows, int num_cols){
  int** C;
  int i,j;
  
  C = malloc(num_rows * sizeof(int*));
  for(i = 0; i < num_rows; i++){
    C[i] = malloc(num_cols * sizeof(int));
    for(j = 0; j < num_cols; j++){
      C[i][j] = A[i][j] + B[i][j];
    }
  }
  
  return C;

}
*/

.global matsum

.equ wordsize, 4

matsum:
  
  #prologue
  push %ebp
  movl %esp, %ebp
  subl $3*wordsize, %esp
  
  .equ A, 2*wordsize #(%ebp)
  .equ B, 3*wordsize #(%ebp)
  .equ num_rows, 4*wordsize #(%ebp)
  .equ num_cols, 5*wordsize #(%ebp)
  .equ C, -1*wordsize #(%ebp)
  .equ i, -2*wordsize #(%ebp)
  .equ j, -3*wordsize #(%ebp)
  
  push %ebx #save ebx
  push %esi #save esi
  
  #EAX is C
  #ECX is i
  #EDX is j
  
  #C = malloc(num_rows * sizeof(int*));
  movl num_rows(%ebp), %eax #get num rows
  shll $2, %eax #num_rows * sizeof(int*)
  push %eax #give malloc its argument
  call malloc #call malloc
  addl $1*wordsize, %esp #remove arguments from stack
  
  #save C
  movl %eax, C(%ebp)
  
  #for(i = 0; i < num_rows; i++)
  
  movl $0, %ecx #i = 0
  
  #set up for the call to malloc
  movl num_cols(%ebp), %ebx #get num_cols
  shll $2, %ebx  #ebx= num_cols * sizeof(int)
  push %ebx
  
  row_loop:
    #i < num_rows
    # i - num_rows < 0
    # negate i - num_rows >= 0
    cmpl num_rows(%ebp), %ecx
    jge end_row_loop
    
    #save i
    movl %ecx, i(%ebp)
    
    #malloc(num_cols * sizeof(int))
    call malloc
    
    #C[i] = malloc(num_cols * sizeof(int))
    movl C(%ebp), %edx #restore C
    movl i(%ebp), %ecx #restore i
    movl %eax, (%edx, %ecx, wordsize) 
    movl %edx, %eax #restoring C still
   
    #for(j = 0; j < num_cols; j++)
    movl $0, %edx
    
    col_loop:
      cmpl num_cols(%ebp), %edx
      jge end_col_loop
    
    
      #C[i][j] = A[i][j] + B[i][j];
      
      #A[i][j]
      movl A(%ebp), %ebx #ebx has A
      movl (%ebx, %ecx, wordsize), %ebx #ebx = A[i]
      movl (%ebx, %edx, wordsize), %ebx #ebx = A[i][j]
      
      #B[i][j]
      movl B(%ebp), %esi #ebx has B
      movl (%esi, %ecx, wordsize), %esi #esi = B[i]
      addl (%esi, %edx, wordsize), %ebx #ebx = A[i][j] + B[i][j]
      
      #C[i][j] = A[i][j] + B[i][j];
      movl (%eax, %ecx, wordsize), %esi #esi = C[i]
      movl %ebx, (%esi, %edx, wordsize) #C[i][j] = A[i][j] + B[i][j]
    
      incl %edx #j++
      jmp col_loop
    end_col_loop:
    incl %ecx #i++
    jmp row_loop
  end_row_loop:
  
  addl $1*wordsize, %esp #remove arguments from stack
  
  #epilogue
  pop %esi #restore old esi
  pop %ebx #restore old ebx
  
  movl %ebp, %esp
  pop %ebp
  ret
  
  
