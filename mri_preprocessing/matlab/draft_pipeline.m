 
mkdir('tmp');
img_path='tmp/'
out_dir='tmp';


reset_orient_mat('b0.nii')
reset_orient_mat('b1000.nii')

run_denoise('b0.nii', 'output');
run_denoise('b1000.nii', 'output');

my_align('b0.nii', 'tmp'); %rigidly
%align b1000 to b0

%apply realign2mni to b0 and b1000 together in the same structure so the second image is kept together with the first. 

run_bb_spm('affine_b0.nii', out_dir, 2)
run_bb_spm('affine_b1000.nii', out_dir, 2)

run_bb_spm('rigid_b0.nii', out_dir, 2)
run_bb_spm('rigid_b1000.nii', out_dir, 2)

non_linear_reg('rigid_b0.nii')

apply_transform('rigid_b0.nii', 'y_rigid_b0.nii', 2, 'w');
apply_transform('rigid_b1000.nii', 'y_rigid_b0.nii', 2, 'w');

