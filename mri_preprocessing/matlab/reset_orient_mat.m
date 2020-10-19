% reset orientation matrix
function [full_path_out] = reset_orient_mat(full_path)
V = spm_vol(full_path);
M = V.mat;
vox = sqrt(sum(M(1:3,1:3).^2));

if det(M(1:3, 1:3)) < 0
    vox(1) = -vox(1); 
end

orig = (V.dim(1:3) + 1) / 2;
off  = -vox.*orig;

M = [vox(1) 0      0      off(1)
     0      vox(2) 0      off(2)
     0      0      vox(3) off(3)
     0      0      0      1];
    
spm_get_space(full_path,M);
full_path_out = full_path;

end

