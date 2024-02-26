#
#                        _oo0oo_
#                       o8888888o
#                       88" . "88
#                       (| -_- |)
#                       0\  =  /0
#                     ___/`---'\___
#                   .' \\|     |// '.
#                  / \\|||  :  |||// \
#                 / _||||| -:- |||||- \
#                |   | \\\  - /// |   |
#                | \_|  ''\---/''  |_/ |
#                \  .-\__  '-'  ___/-. /
#              ___'. .'  /--.--\  `. .'___
#           ."" '<  `.___\_<|>_/___.' >' "".
#          | | :  `- \`.;`\ _ /`;.`/ - ` : | |
#          \  \ `_.   \_ __\ /__ _/   .-` /  /
#      =====`-.____`.___ \_____/___.-`___.-'=====
#                        `=---='

#      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 佛祖保佑 永无Bug
# Buddha bless never down, never bug

### some functions to operate on PDB file

import re
from collections import defaultdict
from pymol_test import *
import numpy as np
import time
import pickle as ppp
from params import aa_dict, aa_reg_str


def pdb_file_reader(pdb_file):
    """
    read pdb file and map xyz coordinates of each residue (input: alphafold pdb or cleaned pdb from pdb_cleaner)
    :param pdb_file:
    :return:
    """
    with open(pdb_file,'r') as f_o:
        file_split = f_o.read().split('\nATOM')[1:]

    residue_atom_xyz = defaultdict(list)
    seq = ''
    residue_pos_start = 0
    # append xyz coords of each atom to residue position
    for line in file_split:

        # dont take hydrogen into account
        if line.split('          ')[1].replace(' ', '') != 'H':
            aa_code = re.search(aa_reg_str, line).group(0)

            residue_pos = int(re.search('\d+(?=\w?\s+[+-]?\d+\.)', line).group())  # positive lookahead

            residue_atom_xyz[residue_pos].append(
                [float(i) for i in re.findall(r'[+-]?\d+\.\d{3}', line)][:3])
            if residue_pos != residue_pos_start:
                seq += aa_dict[aa_code]
                residue_pos_start = residue_pos
        else:
            continue
    # print (residue_atom_xyz)
    return residue_atom_xyz, seq


def reorder_pdb(residue_atom_xyz):
    """
    reorder residue position starting from 1
    :param residue_atom_xyz: defaultdict(list) key order preserved as stack, returned by pdb_file_reader
    :return:
    """
    new_pdb_atom_dict = {}
    start = 1
    for pos in residue_atom_xyz:
        new_pdb_atom_dict[start] = residue_atom_xyz[pos]
        start += 1
    return new_pdb_atom_dict


def pdb_cleaner(pdb_file, cleaned_pdb_file, chain):
    """
    clean a pdb file from RCSB, not alphafold pdbs, based on chain name,
    cleaned pdb could be used as input in pdb_file_reader, or complex pdb could be directly read by complex_pdb_reader
    :param pdb_file:
    :param chain:
    :return: a cleaned pdb only containing the selected chain
    """
    # decide chain case sensitive
    with open(pdb_file, 'r', newline='\n') as f_o:
        f_string = f_o.read()
        fstr_split = f_string.split('\nATOM')[1:]
        filter_f_string = ''.join(fstr_split)

        chain = chain if re.search('[A-Z]{3} ' + chain + ' *\d+', filter_f_string) else chain.lower()

    # write new file
    with open(pdb_file, 'r', newline='\n') as f_open:
        with open(cleaned_pdb_file, 'w', newline='\n') as f_write:
            f_write.write('\n')

            for line in f_open:

                if line.startswith('ATOM') and re.search('[A-Z]{3} ' + chain + ' *\d+', line):
                    f_write.write(line)
                elif line.startswith('TER') and re.search('[A-Z]{3} ' + chain + ' *\d+', line):
                    f_write.write(line)
                    break  # only include one monomer，stop at first TER
                else:
                    continue

    return cleaned_pdb_file


def clean_pdb_reindex(cleaned_pdb_file):
    """
    reindex pdb file from 1, output a new cleaned
    :param cleaned_pdb_file:
    :return:
    """


def pdb_mutiple_reader(pdb_file_list:list):
    """
    read alphafold pdb files corresponding to one protein, because protein too long have multiple alphafold pdb files
    :param pdb_file_list: a list of alphafold pdbs corresponding to one protein entry
    :return:
    """
    residue_atom_xyz = defaultdict(list)

    for pdb in pdb_file_list:
        with open(pdb, 'r') as f_o:
            f_read = f_o.read()
            res_length = int(f_read.split('\nSEQRES')[0].split('    ')[-1].rstrip(' '))
            file_split = f_read.split('\nATOM')[1:]
        for line in file_split:
            residue_atom_xyz[int(re.search('\d+(?=\s+[+-]?\d+\.)', line).group())].append([float(i) for i in re.findall(r'[+-]?\d+\.\d{3}', line)])


def complex_pdb_reader(pdb_file, chain='A'):
    """
    read more complex pdb file, read each residue and 3 coordinates
    :param pdb_file:
    :return:
    """

    residue_atom_xyz = defaultdict(list)

    info_list = []
    with open(pdb_file,'r') as f_o:
        file_read = f_o.read()
        file_split = file_read.split('\nATOM')[1:]  # only read before first TER, e.g. only A chain
        # sometimes lowercase chain name, if found no upper case, change chain to lower case
        chain = chain if re.search('[A-Z]{3} ' + chain + ' *\d+', ''.join(file_split)) else chain.lower()
        # filter_file_split = [l for l in file_split if re.search('[A-Z]{3} ' + chain + ' *\d+', l)]  # filter different chain

        # only include one monomer
        filter_file_split = []
        for l in file_split:

            if re.search('[A-Z]{3} ' + chain + ' *\d+', l) and 'HETATM' not in l:
                if '\nTER' not in l:  # get chunk before first TER
                    filter_file_split.append(l)

                else:
                    filter_file_split.append(l.split('\nTER')[0])
                    break

        last_line = filter_file_split[-1]
        if 'HETATM' in last_line:
            last_line = last_line.split('HETATM')[0]
            for line in filter_file_split[:-1]:
                if re.search(aa_reg_str,line):
                    info_list.append(
                        (re.search(aa_reg_str, line).group(0), int(re.search('\d+(?=\s+[+-]?\d+\.)', line).group()),
                         [float(i) for i in re.findall(r'[+-]?\d+\.\d{3}', line)][:3]))

            # info_list.append((re.search(aa_reg_str,last_line).group(0), int(re.search('\d+(?=\s+[+-]?\d+\.)', line).group()),
            #                   [float(i) for i in re.findall(r'[+-]?\d+\.\d{3}', last_line)]))

        else:
            for line in filter_file_split[:-1]:
                if re.search(aa_reg_str,line):
                    info_list.append(
                        (re.search(aa_reg_str, line).group(0), int(re.search('\d+(?=\s+[+-]?\d+\.)', line).group()),
                         [float(i) for i in re.findall(r'[+-]?\d+\.\d{3}', line)][:3]))

    idx = info_list[0][1]
    seq = aa_dict[info_list[0][0]]  # aa sequence initialize
    for each in info_list:
        res_pos = each[1]  # residue position
        residue_atom_xyz[res_pos].append(each[-1])
        if res_pos != idx:
            seq += aa_dict[each[0]]
            idx = res_pos
    return residue_atom_xyz, seq


def plddt_retrieve(alphafold_pdb):
    """
    get pLDDT value from alphafold pdb file
    :param alphafold_pdb:
    :return:
    """
    with open(alphafold_pdb,'r') as f_o:
        file_split = f_o.read().split('\nATOM')[1:]

        return [float(re.search('\d+\.\d+(?=\s+[A-Z])',line).group()) for line in file_split]


def residue_plddt_retrieve(alphafold_pdb):
    """
    get pLDDT value for each residue number from alphafold pdb
    :param alphafold_pdb:
    :return:
    """
    with open(alphafold_pdb,'r') as f_o:
        file_split = f_o.read().split('\nATOM')[1:]

    return {int(re.search('\d+(?=\s+[+-]?\d+\.)',line).group()):
                          float(re.search('\d+\.\d+(?=\s+[A-Z])',line).group()) for line in file_split}


def find_centroid(residue_atom_xyz, centroid_method='mean'):
    """
    find geometric center of protein given xyz coordinates
    :param residue_atom_xyz:
    :return: use median as centroid
    """
    atom_coordinates = np.array([coord for each in residue_atom_xyz for coord in residue_atom_xyz[each]])

    if centroid_method == 'mean':
        return np.mean(atom_coordinates,axis=0)
    elif centroid_method == 'median':
        return np.median(atom_coordinates,axis=0)


def residue_distance(pdb_file):
    """
    calculate the distance for each residue to center of 3d structure
    :param residue_atom_xyz:
    :param start_pos: first residue start position, alphafold=1, some pdd starts with other than 1
    :return:
    """
    residue_atom_xyz = pdb_file_reader(pdb_file)[0]
    # zero_point = np.array([0,0,0])
    zero_point = find_centroid(residue_atom_xyz)

    residue_distance_dict = {}
    start = 1  # treat first residue as index 1
    # print (residue_atom_xyz)
    for each_pos in residue_atom_xyz:

        total_dist = sum([np.linalg.norm(np.array(each_atom)-zero_point)
                          for each_atom in residue_atom_xyz[each_pos]])

        average_dist = total_dist/len(residue_atom_xyz[each_pos])
        residue_distance_dict[start] = average_dist
        start += 1

    if '-' in pdb_file:
        key = pdb_file.split('\\')[-1].split('-')[1]
    else:
        key = pdb_file.split('/')[-1].split('.pdb')[0]
    print(key + ' done.')
    return {key: residue_distance_dict}


def cov_distance(freq_array,residue_dist_dict):
    """
    calculate averge distance of covered region in one protein
    :param freq_array:
    :param residue_dist_dict:
    :return:
    """

    num_nonzeros = np.count_nonzero(freq_array)
    if num_nonzeros == 0:
        return None
    else:
        # ave_dist = 0
        non_zero_index = np.nonzero(freq_array)[0]
        ave_dist = sum([residue_dist_dict[i+1] for i in non_zero_index])/num_nonzeros
        # for i in non_zero_index:
        #     ave_dist += residue_dist_dict[i+1]

        return ave_dist


def cov_distance_tmt(freq_array, tmt_quant_array, residue_dist_dict):
    """
    use tmt normalized intensity to calculate average distance of cleave-to-center
    :param freq_array:
    :param tmt_quant_array: same length as freq_array, each index has normalized intensity
    :param residue_dist_dict:
    :return:
    """
    num_nonzeros = np.count_nonzero(freq_array)
    if num_nonzeros == 0:
        return None
    else:

        non_zero_index = np.nonzero(freq_array)[0]
        ave_dist = sum([residue_dist_dict[i + 1] * tmt_quant_array[i] for i in non_zero_index]) / num_nonzeros

        return ave_dist


def cov_plddt(freq_array,plddt_dict):
    """
    calculate average plddt of covered region in one protein
    :param freq_array:
    :param plddt_dict:
    :return:
    """
    num_nonzeros = np.count_nonzero(freq_array)
    if num_nonzeros == 0:
        return None
    else:
        # ave_dist = 0
        non_zero_index = np.nonzero(freq_array)[0]
        ave_plddt = sum([plddt_dict[i + 1] for i in non_zero_index]) / num_nonzeros
        # for i in non_zero_index:
        #     ave_dist += residue_dist_dict[i+1]

        return ave_plddt


def cov_dist_normalize(freq_array,residue_dist_dict):
    """
    calculate the normalized distance of covered region in one protein, normalized_dist = dist/max(dist)
    :param freq_array:
    :param residue_dist_dict:
    :return:
    """
    num_nonzeros = np.count_nonzero(freq_array)
    max_dist = max([v for v in residue_dist_dict.values()])
    if num_nonzeros == 0:
        return None
    else:
        ave_dist = 0
        non_zero_index = np.nonzero(freq_array)[0]
        for i in non_zero_index:
            ave_dist += residue_dist_dict[i + 1]/max_dist*100

        return ave_dist / num_nonzeros


def pdb2_3darray(pdb_file):
    """
    convert pdb coordinates into 3d numpy array
    :param pdb_file:
    :return:
    """
    protein_cood_dict = pdb_file_reader(pdb_file)
    normalized_protein_coord_dict = {}

    # average the coordinates of atoms
    for _ in protein_cood_dict:
        locs = np.mean(np.array(protein_cood_dict[_]),axis=0)
        protein_cood_dict[_] = locs

    new_coord_array = np.array([each for each in protein_cood_dict.values()])

    # get x, y, z range
    x_diff,y_diff,z_diff = [(i-j,j) for i, j in zip(np.max(new_coord_array, axis=0), np.min(new_coord_array,axis=0))]

    # normalize x y z coordinates
    for _ in protein_cood_dict:
        x,y,z = protein_cood_dict[_]
        new_x,new_y,new_z = int((x-x_diff[1])*10), int((y-y_diff[1])*10),int((z-z_diff[1])*10)
        print(new_x,new_y,new_z)
        normalized_protein_coord_dict[_-1] = (new_x,new_y,new_z)

    return normalized_protein_coord_dict, [int(x_diff[0]*10), int(y_diff[0]*10), int(z_diff[0]*10)]


def map_aa2_3darray(freq_array, normalized_protein_coord_dict, coord_range_list):
    """
    map aa
    :param freq_array:
    :param normalized_protein_coord_dict:
    :param coord_range_list: [x_range, y_range, z_range], returned by pdb2_3darray second return
    :return:
    """
    x,y,z = coord_range_list
    protein_3d = np.zeros((x+1,y+1,z+1),dtype=np.int8)
    non_zero_index = np.nonzero(freq_array)[0]

    for each in non_zero_index:
        # sequence index to 3d coordinates
        x,y,z = normalized_protein_coord_dict[each]

        protein_3d[x][y][z] +=1
    return protein_3d


def residue_density_cal(input_tuple):
    """
    calculate the number of atoms within a certain range of one residue
    :param alphafold_pdb_file: the alphafold pdb file
    :return:
    """
    time_start = time.time()

    alphafold_pdb_file,protein_seq = input_tuple
    k_density_dict, r_density_dict = {}, {}

    k_index = [m.end() for m in re.finditer(r'K(?=[^P])', protein_seq)]
    r_index = [m.end() for m in re.finditer(r'R(?=[^P])', protein_seq)]

    residue_density_dict = {}
    residue_atom_coord_dict = pdb_file_reader(alphafold_pdb_file)[0]
    # print (residue_atom_coord_dict)
    # residue_xyz_dict = {each:np.mean(residue_atom_coord_dict[each],axis=0) for each in residue_atom_coord_dict}
    xyz_nparray = [v for v in residue_atom_coord_dict.values()]

    # xyz max minus xyz min
    # xyz_range = np.amax(xyz_nparray,axis=0)-np.amin(xyz_nparray,axis=0)

    # check 1/10 of xyz_range for each residue
    # check_range_xyz = xyz_range/10/2

    radius_power2 = 225 # 15A^2 trypsin radius= 1.5 nm
    # for each in residue_atom_coord_dict:
    #
    #     ref = residue_atom_coord_dict[each][-1] # only count C terminal of one residue as ref
    #     # print (ref)
    #
    #     # find CNOS atoms within the radius range
    #     bool_array = [inSphere(j,ref,radius_power2) for i in xyz_nparray for j in i]
    #
    #     # number of CNO atoms within a range for one residue C terminus = number of boolean true - len()
    #     # num_resi_inrange = np.count_nonzero(bool_array)-len(residue_atom_coord_dict[each])
    #     num_resi_inrange = np.count_nonzero(bool_array)
    #     residue_density_dict[each]=num_resi_inrange

    ### get # of density within a range of K/R
    for k in k_index:
        ref = residue_atom_coord_dict[k][-1]
        bool_array = [inSphere(j,ref,radius_power2) for i in xyz_nparray for j in i]
        num_resi_inrange = np.count_nonzero(bool_array)
        k_density_dict[k] = num_resi_inrange
    for r in r_index:
        ref = residue_atom_coord_dict[r][-1]
        bool_array = [inSphere(j,ref,radius_power2) for i in xyz_nparray for j in i]
        num_resi_inrange = np.count_nonzero(bool_array)
        r_density_dict[r] = num_resi_inrange

    # print (time.time()-time_start)
    return {alphafold_pdb_file.split('\\')[-1].split('-')[1]:(k_density_dict,r_density_dict)}


def residue_density_cal2(input_tuple, protease=('trypsin'), radius=15):
    """
    calculate number of atoms within certain range of a residue
    :param input_tuple:
    :param protease:
    :param radius_power2: radius power of protease
    :return:
    """
    # chymotrypsin radius in water =2.1 nm ,reference https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2567952/
    alphafold_pdb_file, protein_seq = input_tuple
    if '-' in alphafold_pdb_file:
        key = alphafold_pdb_file.split('\\')[-1].split('-')[1]
    else:
        key = alphafold_pdb_file.split('/')[-1].split('.pdb')[0]

    from commons import expasy_rules
    time_start = time.time()
    cleavage_density_dict = {}
    # print (alphafold_pdb_file)
    if type(protease) == str:
        cleavage_index = [m.end() for m in re.finditer(expasy_rules[protease], protein_seq)]
    elif type(protease) == tuple:
        cleavage_index = []
        for p in protease:
            cleavage_index += [m.end() for m in re.finditer(expasy_rules[p], protein_seq)]
    else:
        raise KeyError(
            'Protease should either be a string such as "trypsin" or a list such as ["trypsin", "chymotrypsin"]')
    residue_atom_coord_dict = pdb_file_reader(alphafold_pdb_file)[0]
    # residue_atom_coord_dict = reorder_pdb(
    #     residue_atom_coord_dict)  # optional, to reindex to start from 1 and increase continously

    xyz_nparray = [each for v in residue_atom_coord_dict.values() for each in v]  # 2D

    xyz_2d_reshape = np.reshape(xyz_nparray, (-1, 3))  # reshape atom coords into 2d array

    for each in cleavage_index:
        ref = residue_atom_coord_dict[each][-1]
        # bool_array = [inSphere(i, ref, radius*radius) for i in xyz_nparray]
        # num_resi_inrange = np.count_nonzero(bool_array)
        num_resi_inrange = inSphere2(ref, xyz_2d_reshape, radius)
        cleavage_density_dict[each] = num_resi_inrange

    print(key + ' done.')
    # print (f'time used: {time.time()-time_start}')
    return {key: cleavage_density_dict}


def cov_KR_density(mapped_KR_array,KR_index_density_tuple):
    """
    calculate the average covered K/R density
    :param: mapped_KR_array: mapping of start/end for each peptide on a numpy zero array,same length as protein
    :param: KR_index_density_dict: return by residue_density_cal['proteinid']
    :return:
    """
    if type(KR_index_density_tuple) == tuple:
        k_density_dict, r_density_dict = KR_index_density_tuple
        combined_density_dict = k_density_dict | r_density_dict
    elif type(KR_index_density_tuple) == dict:
        combined_density_dict = KR_index_density_tuple
    else:
        raise ValueError('index density should be a tuple of dictionary or dictionary ')
    # print (combined_density_dict)
    combined_density_dict = {int(each): combined_density_dict[each] for each in combined_density_dict}
    num_nonzeros = np.count_nonzero(mapped_KR_array)
    if num_nonzeros == 0:  # no peptides mapped to such protein
        return None
    else:
        non_zero_index = np.nonzero(mapped_KR_array)[0]
        sum_density = 0
        mapped = 0
        for i in non_zero_index:  ## to do, could optimze by list comprehension
            if i + 1 in combined_density_dict:  ## to do, sometimes raise bug
                mapped += 1
                sum_density += combined_density_dict[i + 1]
            else:
                print(f'{i + 1} position not in density dict')
                # pass
        if mapped == 0:  # if real cleavage does not map with any insilico cleavage
            return None
        else:
            # return sum_density/num_nonzeros
            return sum_density / mapped


def cov_KR_density_tmt(mapped_KR_array, tmt_quant_array, KR_index_density_tuple):
    """
    same as cov_KR_density, use tmt int as weight factor
    :param mapped_KR_array:
    :param tmt_array:
    :param KR_index_density_tuple:
    :return:
    """
    if type(KR_index_density_tuple) == tuple:
        k_density_dict, r_density_dict = KR_index_density_tuple
        combined_density_dict = k_density_dict | r_density_dict
    elif type(KR_index_density_tuple) == dict:
        combined_density_dict = KR_index_density_tuple
    else:
        raise ValueError('index density should be a tuple of dictionary or dictionary ')
    # print (combined_density_dict)
    num_nonzeros = np.count_nonzero(mapped_KR_array)
    if num_nonzeros == 0:  # no peptides mapped to such protein
        return None
    else:
        non_zero_index = np.nonzero(mapped_KR_array)[0]
        sum_density = 0
        mapped = 0
        for i in non_zero_index:  ## to do, could optimze by list comprehension
            if i + 1 in combined_density_dict:  ## to do, sometimes raise bug
                mapped += 1
                sum_density += combined_density_dict[i + 1] * tmt_quant_array[i]
            else:
                print(f'{i + 1} position not in density dict')
                # pass
        if mapped == 0:  # if real cleavage does not map with any insilico cleavage
            return None
        else:
            # return sum_density/num_nonzeros
            return sum_density / mapped


def inSphere(point, ref, radius_power2):
    diff = np.subtract(point, ref)  # [(x1-x2),(y1-y2), (z1-z2)]
    # print (diff)
    dist = np.sum(np.power(diff, 2))  # sum of square of difference
    # print (dist)
    # If dist is less than radius^2, return True, else return False
    return dist < radius_power2


def inSphere2(ref, atoms, radius):
    """
    faster than inSphere, calculate multiple atoms at once
    :param ref: reference point
    :param atoms: atoms in the filtered cube space, 2D numpy array
    :param radius:
    :return: number of atoms in the sphere radius
    """
    ### filter surrounding atoms in a cube with equivalent radius
    # atoms = np.array(atoms) if not type(atoms) == np.ndarray else atoms

    cube_edge_upper, cubu_edge_lower = np.sum([ref, [radius, radius, radius]], axis=0), \
                                       np.sum([ref, [-radius, -radius, -radius]], axis=0)
    # get atoms inside the cube, lower edge<atom<upper edge

    filtered_atoms = [np.sum(each <= cube_edge_upper) == 3 and
                      np.sum(each >= cubu_edge_lower) == 3 for each in atoms]
    filtered_atoms_number = np.sum(filtered_atoms)
    # print(f'orginal number of atoms: {len(atoms)}, after filter: {filtered_atoms_number}')

    filtered_atoms_coords = atoms[np.array(filtered_atoms)]

    ### check if in the sphere, calculate euclidean distance
    distance_array = np.linalg.norm(filtered_atoms_coords - np.tile(ref, [filtered_atoms_number, 1]), axis=1)

    return len(np.where(distance_array <= radius)[0])


def read_pdb_fasta(pdb_fasta):
    """
    read residue sequence from pdb fasta
    :param pdb_fasta:
    :return:
    """
    with open(pdb_fasta, 'r') as f:
        f_split = f.read().split('>')[1:]
        sequence = ''.join([each.split('\n')[-2] for each in f_split])
    return sequence


def sasa_pdb(input_tuple, protease='trypsin'):
    """
    compute solvent accessible surface area (SASA) given a pdb file
    :param pdb_file:
    :return:
    """
    import pymol
    from commons import expasy_rules
    pdb_file, protein_seq = input_tuple
    cleavage_index = [m.end() for m in re.finditer(expasy_rules[protease], protein_seq)]

    # pymol.pymol_argv = ['pymol', '-qc']  # pymol launching: quiet (-q), without GUI (-c)
    # pymol.finish_launching()

    pymol.cmd.set('dot_solvent', 1)
    pymol.cmd.set('dot_density', 3)  # surface area
    pymol.cmd.set('solvent_radius', 15)  # same radius as trypsin

    pdb_name = os.path.split(pdb_file)[1]
    pymol.cmd.load(pdb_file, pdb_name)
    # residues = []
    # cmd.iterate('all', 'residues.append(resi)') # iterate residues and store into the list

    residue_sasa_dict = {}
    for i in cleavage_index:
        residue_sasa_dict[i] = pymol.cmd.get_area('resi %s' % i)
    pymol.cmd.delete(pdb_name)
    print(pdb_file + ' done')
    return {pdb_file.split('\\')[-1].split('-')[1]: residue_sasa_dict}


def atom_density_center(alphafold_pdb, radius: float):
    """
    calculate density center given a pdb structure # too slow, need to optimize
    :param alphafold_pdb:
    :param radius: radius of the cube
    :return: the coordinate of density center
    """
    time_start = time.time()
    residue_atom_coord_dict = pdb_file_reader(alphafold_pdb)
    xyz_nparray = [each for v in residue_atom_coord_dict.values() for each in v]  # atom coordinates in 2D
    result_dict = defaultdict(list)

    for atom in xyz_nparray:
        cube_edge_upper, cubu_edge_lower = np.sum([atom, [radius, radius, radius]], axis=0), \
                                           np.sum([atom, [-radius, -radius, -radius]], axis=0)
        filtered_atoms = [np.sum(each <= cube_edge_upper) == 3 and
                          np.sum(each >= cubu_edge_lower) == 3 for each in xyz_nparray]
        num_filterd_atoms = np.sum(filtered_atoms)
        # print (num_filterd_atoms,atom)
        result_dict[num_filterd_atoms].append(atom)
    print(f"time used: {time.time() - time_start}")
    return sorted(result_dict.items())


if __name__ == '__main__':
    import time
    import pickle
    import pandas as pd
    import matplotlib.pyplot as plt
    pdb_file = 'D:/data/alphafold_pdb/UP000005640_9606_HUMAN/AF-Q9H2X0-F1-model_v1.pdb'
    fasta_file = 'D:/data/pats/human_fasta/uniprot-proteome_UP000005640_sp_tr.fasta'
    protein_dict = fasta_reader(fasta_file)
    alphafold_protein_dict = pickle.load(open('D:/data/alphafold_pdb/human_alpha_seq_dict.p', 'rb'))

    """
    time_point_rep = ['1h','2h','4h','18h']
    psm_tsv_list = ['D:/data/native_protein_digestion/' + each + '_1_native/psm.tsv' for each in time_point_rep]
    print(f'{len(psm_tsv_list)} psm files to read...')
    
    # peptide_list = peptide_counting(peptide_tsv)
    
    psm_list = [psm for file in psm_tsv_list for psm in modified_peptide_from_psm(file)]

    # time_start = time.time()
    # residue_distance = residue_distance(pdb_file_reader(pdb_file))
    # print (time.time()-time_start)
    # print (residue_distance)
    freq_array = freq_ptm_index_gen_batch_v2(psm_list,protein_dict)[0]['P61604']
    normalized_prot_dict, xyz_list = pdb2_3darray(pdb_file)
    print (xyz_list)
    mapped_3darray = map_aa2_3darray(freq_array,normalized_prot_dict,xyz_list)
    flat_array = mapped_3darray.flatten()
    print (np.count_nonzero(flat_array))
    #
    # print (cov_distance(freq_array,residue_distance))

    """
    alphafold_base = 'D:/data/alphafold_pdb/UP000005640_9606_HUMAN/'
    pdb_base = 'F:/full_cover_pdbs/'
    ### get unique peptide dict

    from commons import get_unique_peptide, psm_reader, protein_tsv_reader, get_aggre_peptide

    #
    # df_prot_pdb = pd.read_csv('C:/tools/seqmappdb/human/fully_covered_unique_PDB.csv')
    # uniprot_pdb_dict = {prot.split('>')[1]: '_'.join(pdb.split('>')[1].split('_')[:2])
    #                     for prot, pdb in zip(df_prot_pdb['queryID'], df_prot_pdb['pdbchainID'])}
    # protein_tsv = 'F:/native_digestion/01202023/search/combined_protein.tsv'
    # protein_list = protein_tsv_reader(protein_tsv, protein_column=1)
    # sub_protein_dict = {prot:protein_dict[prot] for prot in protein_list}
    # pdb_seq_dict = ppp.load(open('F:/full_cover_pdbs/pdb_seq_dict.p', 'rb'))
    # sub_protein_dict = {}
    # for prot in protein_list:
    #     if prot in uniprot_pdb_dict:
    #         pdb_name = uniprot_pdb_dict[prot]
    #         sub_protein_dict[prot+'_'+pdb_name] = pdb_seq_dict[pdb_name]


    ### pdb protein dictionary

    base_path = 'D:/data/native_protein_digestion/12072021/heat_shock_ionquant_MBR/'
    folders = [base_path + folder for folder in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, folder))]
    time_points = [each.split('/')[-1] for each in folders]
    pep_path_list = [each + '/peptide.tsv' for each in folders]
    # psm_path_list = [each + '/psm.tsv' for each in folders]
    unique_peptide_dict = get_unique_peptide(pep_path_list)
    # aggre_peptide_dict = get_aggre_peptide(pep_path_list)
    # print([(each, len(unique_peptide_dict[each])) for each in unique_peptide_dict])
    # print ([(each, len(peptide_counting(each))) for each in pep_path_list])
    # for each in psm_path_list:
    #     psm_dict = psm_reader(each)
    #     print(each, sum([psm_dict[pep] for pep in psm_dict]))

    # print(f'{len(psm_path_list)} psm files to read...')

    ### single protein analysis
    """
    pdb_base_path = 'D:/data/alphafold_pdb/UP000005640_9606_HUMAN/'
    base_path = 'D:/data/native_protein_digestion/10282021/search_result_4miss/h20/'
    folders = glob(base_path + '*h2o/')

    time_points = [each.split('\\')[-2] for each in folders]
    print(time_points)
    ### get KR to centroid distance and density profile for single protein
    sub_protein_dict = {'Q02543': protein_dict['Q02543']}

    from commons import get_unique_peptide

    psm_dict = get_unique_peptide(glob(base_path + '/*/peptide.tsv'))

    pdb_file_path = pdb_base + 'AF-' + 'Q02543' + '-F1-model_v1.pdb'
    # pdb_file_path = 'D:/data/pdb/AF-Q02543-rosettamodel.pdb'
    KR_density_dict = residue_density_cal((pdb_file_path, protein_dict['Q02543']))


    for time in time_points:
        print(time)
        freq_array_dict = mapping_KR_toarray(psm_dict[time], sub_protein_dict)
        residue_dist_dict = residue_distance(pdb_file_reader(pdb_file_path))
        freq_array = freq_array_dict['Q02543']

        cov_dist = cov_distance(freq_array, residue_dist_dict)
        # ave_KR_density = cov_KR_density(freq_array, KR_density_dict['Q02543'])
        print(cov_dist)
    """
    ### calculate covered distance/average pLDDT and write to excel

    distance_dict = pickle.load(open('F:/native_digestion/01242023/time_points/to_center_distance_dict.pkl', 'rb'))
    prot_list_heatshock = \
    pd.read_csv('D:/data/native_protein_digestion/12072021/heat_shock_ionquant_MBR/combined_protein.tsv'
                , sep='\t', index_col=0)['Protein ID'].tolist()
    protein_list = [each for each in prot_list_heatshock if each in distance_dict]
    # protein_list = [p for p in distance_dict]
    # unique_pep_dict = pickle.load(open('F:/native_digestion/01242023/time_points/f_peptides_dict.p', 'rb'))
    # f_list = ['tryps_0005min', 'tryps_0010min', 'tryps_0015min', 'tryps_0020min', 'tryps_0030min', 'tryps_0040min',
    #           'tryps_0050min', 'tryps_0060min', 'tryps_0120min', 'tryps_0180min', 'tryps_0240min', 'tryps_1440min',
    #           'tryps_leftover']
    sub_protein_dict = {p: protein_dict[p] for p in protein_list}
    df = pd.DataFrame(index=protein_list, columns=time_points)  # some protein entry does not have pdb

    # df = pd.DataFrame(index=protein_list, columns=f_list)
    for pep_tsv in pep_path_list:
        # for pep_tsv in f_list:
        print (pep_tsv)
        # peptide_list = peptide_counting(pep_tsv)
        peptide_list = unique_peptide_dict[pep_tsv.split('/')[-2]]
        # peptide_list = aggre_peptide_dict[pep_tsv.split('/')[-2]]
        # peptide_list = unique_pep_dict[pep_tsv]
        # if peptide_list:
        freq_array_dict = mapping_KR_toarray(peptide_list, sub_protein_dict)[0]
        for prot in protein_list:
            pdb_file_path = alphafold_base + 'AF-' + prot + '-F1-model_v1.pdb'
            if os.path.exists(pdb_file_path):
            # if prot in uniprot_pdb_dict: # if prot has full pdb coverage
                if len(alphafold_protein_dict[pdb_file_path.split('/')[-1]]) == len(protein_dict[prot]):
                    # pdb_file_path = pdb_base+uniprot_pdb_dict[prot]+'_clean.pdb'
                    # print (pdb_file_path)
                    # print (pdb_seq_dict[uniprot_pdb_dict[prot]])
                    # residue_dist_dict = residue_distance(pdb_file_reader(pdb_file_path)[0])
                    # plddt_dict = residue_plddt_retrieve(pdb_file_path)
                    # if len(residue_dist_dict) == len(protein_dict[prot]):  # filter out those really long proteins

                    # if len(plddt_dict) == len(protein_dict[prot]):
                    freq_array = freq_array_dict[prot]
                    # freq_array = freq_array_dict[prot + '_' + uniprot_pdb_dict[prot]]
                    # print (np.count_nonzero(freq_array))
                    cov_dist = cov_distance(freq_array, distance_dict[prot])
                    # print (cov_dist)
                    # ave_cov_plddt = cov_plddt(freq_array,plddt_dict)
                    # df.at[prot + '_' + uniprot_pdb_dict[prot], pep_tsv.split('/')[-2]] = cov_dist
                    df.at[prot, pep_tsv.split('/')[-2]] = cov_dist
                    # df.at[prot, pep_tsv] = cov_dist
                    # else:
                    #     print('%s protein len between pdb and fasta is not same' % prot)
                else:
                    df.at[prot, pep_tsv.split('/')[-2]] = np.nan
                    # df.at[prot, pep_tsv] = np.nan
                    print (f'{prot} not mapped to pdb')
                    continue
        # else:
        #     for prot in protein_list:
        #         df.at[prot, pep_tsv.split('/')[-2]] = np.nan
    df.to_excel('D:/data/native_protein_digestion/12072021/heat_shock_ionquant_MBR/distance_to_center_all.xlsx')

    ### calculate coverage distance/density from tmt data
    """
    tmt1 = 'F:/native_digestion/Uchicago_TMT/tmt_search_0826/TMT1/protein.tsv'
    tmt2 = 'F:/native_digestion/Uchicago_TMT/tmt_search_0826/TMT2/protein.tsv'
    tmt3 = 'F:/native_digestion/Uchicago_TMT/tmt_search_0826/TMT3/protein.tsv'
    tmt_df = pd.read_csv('F:/native_digestion/Uchicago_TMT/tmt_search_0826/tmt_convert_95quantile.tsv',
                         delimiter='\t', index_col=0)
    tmt_protein_list = pd.read_csv(tmt1, sep='\t', index_col=0)['Protein ID'].tolist() + \
                       pd.read_csv(tmt2, sep='\t', index_col=0)['Protein ID'].tolist() + \
                       pd.read_csv(tmt3, sep='\t', index_col=0)['Protein ID'].tolist()
    tmt_protein_list = set(tmt_protein_list)

    print(len(tmt_protein_list))
    tmt_protein_dict = {each: protein_dict[each] for each in tmt_protein_list}
    tmt_columns = [each for each in tmt_df.columns]
    print(tmt_columns)
    time.sleep(3)
    tmt_peptide_list = tmt_df.index.tolist()
    # KR_density_alpha_dict = pickle.load(
    #     open('D:/data/alphafold_pdb/trypsin_clea_atom_density/tmt_tryp_chymo_15A_cleavage_density_dict.pkl', 'rb'))
    distance_dict = pickle.load(open('D:/data/alphafold_pdb/tmt_distance_dict.pkl', 'rb'))
    new_df = pd.DataFrame(index=tmt_protein_list, columns=tmt_columns)
    for column in tmt_columns:

        print(column)
        count = 0
        TMT_int_list = tmt_df[column].tolist()
        TMT_dict = {pep: tmt for pep, tmt in zip(tmt_peptide_list, TMT_int_list) if
                    tmt != 0}  # filter out peptides with no intensity
        filtered_peptide_list = [k for k in TMT_dict.keys()]
        print(f"peptide list length: {len(filtered_peptide_list)}")
        freq_array_dict, freq_index_dict, tmt_array_dict = mapping_KR_toarray(filtered_peptide_list, tmt_protein_dict,
                                                                              TMT=TMT_dict)
        for prot in tmt_protein_list:
            # print (prot)
            count += 1
            print(f'{len(tmt_protein_list) - count} proteins to go in {column}')

            pdb_file_path = alphafold_base + 'AF-' + prot + '-F1-model_v1.pdb'
            if os.path.exists(pdb_file_path):
                # plddt_dict = residue_plddt_retrieve(pdb_file_path)
                # if len(residue_dist_dict) == len(protein_dict[prot]):  # filter out those really long proteins
                if len(alphafold_protein_dict[pdb_file_path.split('/')[-1]]) == len(protein_dict[prot]):
                    # if len(plddt_dict) == len(protein_dict[prot]):
                    freq_array, tmt_array = freq_array_dict[prot], tmt_array_dict[prot]

                    cov_dist = cov_distance_tmt(freq_array, tmt_array, distance_dict[prot])
                    new_df.at[prot, column] = cov_dist
                    # ave_KR_density = cov_KR_density_tmt(freq_array, tmt_array, KR_density_alpha_dict[prot])
                    # new_df.at[prot, column] = ave_KR_density
                else:
                    print('%s protein len between pdb and fasta is not same' % prot)
            else:
                print(f'{prot} does not have a pdb file.')
                continue
    new_df.to_csv('F:/native_digestion/Uchicago_TMT/tmt_search_0826/distance_11_13_2.tsv', sep='\t')
    """
    """
    
    from statistics import mean
    import random
    # prots_tocheck = random.sample(protein_list,100)
    prots_tocheck = [each.split('\\')[-1].split('.png')[0] for each in glob('D:/data/native_protein_digestion/10282021/protein_centroid/*')]
    print (prots_tocheck)
    """

    ### calculate covered K/R density and write to excel
    """
    from pymol_test import mapping_KR_toarray
    import json

    df = pd.DataFrame(index=protein_list, columns=f_list)  # some protein entry does not have pdb
    # solven_acc_dict = json.load(open(r'F:\native_digestion\alphafold_pdbs_sasa\sasa_area30A_total_dict.json', 'r'))
    # solven_acc_dict = pickle.load(open('D:/data/alphafold_pdb/1207control_protein_KR_sasa_dict.pkl','rb'))
    KR_density_alpha_dict = pickle.load(
        open('F:/native_digestion/01242023/analysis/trypsin_atom_density_dict.pkl', 'rb'))
    existed_density_dict = ppp.load(open('F:/native_digestion/12092022/analysis/trypsin_pymol_density_dict.pkl', 'rb'))
    KR_density_alpha_dict.update(existed_density_dict)
    # chymo_cleav_density_dict = pickle.load(
    #     open('D:/data/alphafold_pdb/688_prot_chymotry_cleave_density_dict.pkl', 'rb'))
    for pep_tsv in f_list:
        print(pep_tsv)
        # peptide_list = peptide_counting(pep_tsv)
        # peptide_list = aggre_peptide_dict[pep_tsv.split('/')[-2]]
        peptide_list = unique_pep_dict[pep_tsv]
        freq_array_dict, freq_array_index_dict = mapping_KR_toarray(peptide_list, sub_protein_dict)
        for prot in protein_list:
            print (prot)
            pdb_file_path = alphafold_base + 'AF-' + prot + '-F1-model_v1.pdb'

            if os.path.exists(pdb_file_path):
                # residue_dist_dict = residue_distance(pdb_file_reader(pdb_file_path))
                # plddt_dict = residue_plddt_retrieve(pdb_file_path)
                # solvent_access_dict = solven_acc_dict[prot]
                # if len(residue_dist_dict) == len(protein_dict[prot]):  # filter out those really long proteins
                if len(alphafold_protein_dict[pdb_file_path.split('/')[-1]]) == len(protein_dict[prot]):
                    freq_array = freq_array_dict[prot]
                    ave_KR_density = cov_KR_density(freq_array, KR_density_alpha_dict[prot])
                    # ave_solvent_access = cov_KR_density(freq_array, solvent_access_dict)
                    df.at[prot, pep_tsv] = ave_KR_density
                    # df.at[prot, pep_tsv.split('/')[-2]] = ave_KR_density
                    # df.at[prot, pep_tsv.split('/')[-2]] = ave_solvent_access
                    # df.at[prot, pep_tsv.split('/')[-2]] = freq_array_index_dict[prot]
                else:
                    print('%s protein len between pdb and fasta is not same' % prot)
            else: 
                continue
    df.to_excel('F:/native_digestion/01242023/analysis/density_15A_radius.xlsx')
    """

    ### plot 3d and centroid
    """
    from matplotlib import animation


    def rotate(angle):
        ax.view_init(azim=angle)


    # for prot in prots_tocheck:
    for prot in ['P41091']:
        pdb_file_path = pdb_base+'AF-'+prot+'-F1-model_v1.pdb'

        if os.path.exists(pdb_file_path):
            fig = plt.figure()
            ax = fig.add_subplot(projection='3d')
            print (prot)

            residue_atom_xyz = pdb_file_reader(pdb_file_path)
            # finding coordinates of K and R
            k_ind, r_ind = [m.end() for m in re.finditer(r'K(?=[^P])', protein_dict[prot])], \
                           [m.end() for m in re.finditer(r'R(?=[^P])', protein_dict[prot])]

            k_x, k_y, k_z = zip(*[each for ind in k_ind for each in residue_atom_xyz[ind]])
            r_x, r_y, r_z = zip(*[each for ind in r_ind for each in residue_atom_xyz[ind]])

            # plot all atoms
            # xyz = [each for v in residue_atom_xyz.values() for each in v]

            # get xyz of atoms other than K and R
            xyz = [each for ind in residue_atom_xyz if ind not in k_ind + r_ind for each in residue_atom_xyz[ind]]
            x,y,z = zip(*xyz)

            ax.scatter(x,y,z,marker='o',s=0.5)

            # highlght K and R
            ax.scatter(k_x, k_y, k_z, marker='o', s=0.5, color='green')
            ax.scatter(r_x, r_y, r_z, marker='o', s=0.5, color='orange')

            centroid = find_centroid(residue_atom_xyz)
            # plot centroid
            ax.scatter([centroid[0]],[centroid[1]],[centroid[2]], marker='o', s=8,color='r')
            ax.text2D(0.05, 0.95, "centroid coordinates: %.2f,%.2f,%.2f" % (centroid[0] ,centroid[1],centroid[2]), transform=ax.transAxes)
            ax.set_xlabel('X axis')
            ax.set_ylabel('Y axis')
            ax.set_zlabel('Z axis')

            # Get rid of colored axes planes
            # First remove fill
            ax.xaxis.pane.fill = False
            ax.yaxis.pane.fill = False
            ax.zaxis.pane.fill = False

            # Now set color to white (or whatever is "invisible")
            # ax.xaxis.pane.set_edgecolor('w')
            # ax.yaxis.pane.set_edgecolor('w')
            # ax.zaxis.pane.set_edgecolor('w')

            # Bonus: To get rid of the grid as well:
            ax.grid(False)
            # make gif
            rot_animation = animation.FuncAnimation(fig, rotate, frames=np.arange(0, 362, 2), interval=150)
            rot_animation.save('D:/data/native_protein_digestion/10282021/protein_centroid_median/%s.gif' % prot,
                               dpi=300, writer='imagemagick')
            # plt.show()
            # plt.savefig('D:/data/native_protein_digestion/10282021/protein_centroid_median/%s.png' % prot, dpi=300)
    """

    ### plot residue distance distribution
    """
    bot,med,top,all = [],[],[],[]
    for prot in prots_tocheck:
        pdb_file_path = pdb_base + 'AF-' + prot + '-F1-model_v1.pdb'

        if os.path.exists(pdb_file_path):
            distance_array = sorted([v for v in residue_distance(pdb_file_reader(pdb_file_path)).values()])
            block = int(len(distance_array)*0.33)
            top_33,med_33,bot_33 = distance_array[-block:],distance_array[block:-block],distance_array[:block]
            bot.append(mean(bot_33))
            med.append(mean(med_33))
            top.append(mean(top_33))
            all.append(mean(distance_array))
            # fig, axs = plt.subplots(2,2)
            # for row,col,data,title in zip([0,0,1,1],[0,1,0,1],
            #                               [bot_33,med_33,top_33,distance_array],['bottom 33%','med 33%','top 33%','all']):
            #     axs[row,col].hist(data,bins=25,alpha=0.8,color='black',density=False)
            #     axs[row,col].set_title(title)
            #     axs[row,col].set_xlabel('Distance')
            #     axs[row,col].set_ylabel('frequency')
            # fig.tight_layout()
            # plt.savefig('D:/data/native_protein_digestion/10282021/distance_distribution_100prots/%s.png' % prot)
            # plt.close(fig)

    fig, axs = plt.subplots(2,2)
    for row,col,data,title in zip([0,0,1,1],[0,1,0,1],
                                  [bot,med,top,all],['bottom 33%','med 33%','top 33%','all']):
        axs[row,col].hist(data,bins=20,alpha=0.8,color='black',density=False)
        axs[row,col].set_title(title)
        axs[row,col].set_xlabel('Distance')
        axs[row,col].set_ylabel('frequency')
    fig.suptitle('Random 100 proteins average residue distance distribution', fontsize=12)
    plt.show()
    """

    ### extract pLDDT from all human alphafold pdbs

    import pickle
    from glob import glob

    # existed_density_dict = ppp.load(open('F:/native_digestion/12092022/analysis/trypsin_pymol_density_dict.pkl', 'rb'))
    # protein_list = pickle.load(open('F:/native_digestion/01242023/time_points/proteinid_set.p', 'rb'))
    # protein_list = [prot for prot in protein_list if prot not in existed_density_dict]
    # pdb_path = 'D:/data/alphafold_pdb/UP000005640_9606_HUMAN/'
    # pdb_files = glob(pdb_path + '*F1*.pdb')
    # pdb_files = [pdb_path + 'AF-' + each + '-F1-model_v1.pdb' for each in protein_list if
    #              os.path.exists(pdb_path + 'AF-' + each + '-F1-model_v1.pdb')]
    # input_list_tuples = [(pdb, alphafold_protein_dict[pdb.split('/')[-1]]) for pdb in pdb_files]
    # print(len(input_list_tuples))
    """   
    count = 0
    # total_array = []
    pdb_plddt_dict = {}
    for each_pdb in pdb_files:
        count += 1
        print(count)
        pdb_plddt_dict[each_pdb.split('/')[-1].split('-')[1]] = plddt_retrieve(each_pdb)
        # total_array.append(plddt_retrieve(each_pdb))
    # pickle.dump(total_array,open('D:/data/alphafold_pdb/pLDDT_human_2d.pkl','wb'))
    pickle.dump(pdb_plddt_dict,open('D:/data/alphafold_pdb/pLDDT_human_dict.pkl','wb'))
    """
    import multiprocessing
    ### calculate residue density for each alphafold pdb, using multiple cpu cores

    # start = time.time()
    # with multiprocessing.Pool(multiprocessing.cpu_count() - 2) as pool:
    #     result = pool.map(residue_density_cal2, input_list_tuples, chunksize=50)
    #     pool.close()
    #     pool.join()
    # file_density_dict = {k: v for d in result for k, v in d.items()}
    #
    # pickle.dump(file_density_dict, open(
    #     'F:/native_digestion/01242023/analysis/trypsin_atom_density_dict.pkl', 'wb'))
    # print(time.time() - start)

    # k_r_density_dict = pickle.load(open('D:/data/alphafold_pdb/human_file_KR_density_dict.pkl','rb'))
    # print (k_r_density_dict['Q8IXR9'])

    # KR_mapped_dict = mapping_KR_toarray(unique_peptide_dict[psm_path_list[1].split('/')[-2]],protein_dict)

    ### calculate solvent accessible surface area (sasa)
    """
    import multiprocessing

    start = time.time()
    with multiprocessing.Pool(multiprocessing.cpu_count() - 2) as pool:
        result = pool.map(sasa_pdb, input_list_tuples, chunksize=50)
        pool.close()
        pool.join()
    file_density_dict = {k: v for d in result for k, v in d.items()}

    pickle.dump(file_density_dict, open('D:/data/alphafold_pdb/1207control_protein_KR_sasa_dict.pkl', 'wb'))
    print(time.time() - start)
    """
    ### calcualte distance with multiple CPUs
    """
    # protein_list = protein_tsv_reader('F:/native_digestion/11112022/search/combined_protein.tsv', protein_column=1)
    protein_list = pickle.load(open('F:/native_digestion/01242023/time_points/proteinid_set.p','rb'))
    pdb_files = [pdb_path + 'AF-' + each + '-F1-model_v1.pdb' for each in protein_list if
                              os.path.exists(pdb_path + 'AF-' + each + '-F1-model_v1.pdb')]
    print (f'{len(pdb_files)} pdb files to process...')
    start = time.time()
    print (f'In total {multiprocessing.cpu_count()}')
    with multiprocessing.Pool(multiprocessing.cpu_count() - 4) as pool:
        result = pool.map(residue_distance, pdb_files, chunksize=50)
        pool.close()
        pool.join()
    file_distance_dict = {k: v for d in result for k, v in d.items()}
    pickle.dump(file_distance_dict, open(
        'F:/native_digestion/01242023/time_points/to_center_distance_dict.pkl', 'wb'))
    """
    ### testing cleavage density algorithms

    # print(input_list_tuples[0])
    # print (residue_density_cal2(input_list_tuples[0]))
