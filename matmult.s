

	.global matMult

	.equ wordsize, 4

matMult:
	//	int** matMult(int **a, int num_rows_a, int num_cols_a, int** b, int num_rows_b, int num_cols_b)

	push %ebp
	movl %esp, %ebp
	subl $6*wordsize, %esp

	.equ a, 2*wordsize
	.equ num_rows_a, 3*wordsize
	.equ num_cols_a, 4*wordsize
	.equ b, 5*wordsize
	.equ num_rows_b, 6*wordsize
	.equ num_cols_b, 7*wordsize
	//	  int row, col, check, sum = 0;
	.equ product, -1*wordsize
	.equ row, -2*wordsize
	.equ col, -3*wordsize
	.equ check, -4*wordsize
	.equ sum, -5*wordsize
	.equ holderj, -6*wordsize
	//int** product = malloc(sizeof(int*) * num_rows_a);
	push %ebx
	push %esi
	push %edi
	movl $0, sum(%ebp)
	
	movl num_rows_a(%ebp), %eax
	shll $2, %eax
	push %eax
	call malloc
	addl $1*wordsize, %esp
	movl %eax, product(%ebp)
	//  for (row = 0; row < num_rows_a; row++)
	movl $0, %ecx
//         product[row] = malloc(sizeof(int) * num_cols_b);
	movl num_cols_b(%ebp), %ebx
	shll $2, %ebx
	push %ebx

row_loop:
	cmpl num_rows_a(%ebp), %ecx
	jge end_row_loop
	movl %ecx, row(%ebp)
	call malloc
	movl product(%ebp), %edx
	movl row(%ebp), %ecx
	movl %eax, (%edx, %ecx, wordsize)
	movl %edx, %eax
	//      for (col = 0; col < num_cols_b; col++)
	movl $0, %edx

col_loop:
	cmpl num_cols_b(%ebp), %edx
	jge end_col_loop

	//		  for (check = 0; check < num_cols_a; check++)
	movl $0, %esi
check_loop:
	cmpl num_cols_a(%ebp), %esi
	jge end_check_loop
	//	      sum += a[row][check] * b[check][col];

        movl %eax, product(%ebp)
	movl a(%ebp), %eax
	movl (%eax, %ecx, wordsize), %eax
	movl (%eax, %esi, wordsize), %eax

	movl b(%ebp), %edi
	movl (%edi, %esi, wordsize), %edi
	movl (%edi, %edx, wordsize), %edi

	movl %edx, holderj(%ebp)
	imull %edi
	movl holderj(%ebp), %edx
	addl %eax, sum(%ebp)

	movl product(%ebp), %eax
	incl %esi
	jmp check_loop
	
	
end_check_loop:
	//product[row][col] = sum;
	//	  sum = 0;
	movl sum(%ebp), %ebx
	movl product(%ebp), %edi
	movl (%edi, %ecx, wordsize), %edi
	movl %ebx, (%edi, %edx, wordsize)
	movl $0, sum(%ebp)
	incl %edx
	jmp col_loop

end_col_loop:
	incl %ecx
	jmp row_loop
	
	

end_row_loop:
	addl $1*wordsize, %esp

	movl product(%ebp), %eax
	pop %edi
	pop %esi
	pop %ebx

	movl %ebp, %esp
	pop %ebp
	ret
	
	
