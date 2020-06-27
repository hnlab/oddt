"""Module calculates interactions between two molecules
(proein-protein, protein-ligand, small-small).
Currently following interacions are implemented:
    * hydrogen bonds
    * halogen bonds
    * pi stacking (parallel and perpendicular)
    * salt bridges
    * hydrophobic contacts
    * pi-cation
    * metal coordination
    * pi-metal
"""

import numpy as np
from oddt.spatial import angle, angle_2v, distance

__all__ = ['close_contacts',
           'hbond_acceptor_donor',
           'hbonds',
           'halogenbond_acceptor_halogen',
           'halogenbonds',
           'pi_stacking',
           'salt_bridge_plus_minus',
           'salt_bridges',
           'hydrophobic_contacts',
           'pi_cation',
           'acceptor_metal',
           'pi_metal']

BASE_ANGLES = np.array((0, 180, 120, 109.5, 90), dtype=float)


def close_contacts(x, y, cutoff, x_column='coords', y_column='coords',
                   cutoff_low=0.):
    """Returns pairs of atoms which are within close contac distance cutoff.
    The cutoff is semi-inclusive, i.e (cutoff_low, cutoff].

    Parameters
    ----------
    x, y : atom_dict-type numpy array
        Atom dictionaries generated by oddt.toolkit.Molecule objects.

    cutoff : float
        Cutoff distance for close contacts

    x_column, ycolumn : string, (default='coords')
        Column containing coordinates of atoms (or pseudo-atoms,
        i.e. ring centroids)

    cutoff_low : float (default=0.)
        Lower bound of contacts to find (exclusive). Zero by default.
        .. versionadded:: 0.6

    Returns
    -------
    x_, y_ : atom_dict-type numpy array
        Aligned pairs of atoms in close contact for further processing.
    """
    if len(x[x_column]) > 0 and len(x[x_column]) > 0:
        d = distance(x[x_column], y[y_column])
        index = np.argwhere((d > cutoff_low) & (d <= cutoff))
        return x[index[:, 0]], y[index[:, 1]]
    else:
        return x[[]], y[[]]


def _check_angles(angles, hybridizations, tolerance):
    """Helper function for checking if interactions are strict"""
    angles = np.nan_to_num(angles)  # NaN's throw warning on comparisons
    ideal_angles = np.take(BASE_ANGLES, hybridizations)[:, np.newaxis]
    lower_bound = ideal_angles - tolerance
    upper_bound = ideal_angles + tolerance
    return ((angles > lower_bound) & (angles < upper_bound)).any(axis=-1)


def hbond_acceptor_donor(mol1, mol2, cutoff=3.5, tolerance=30):
    """Returns pairs of acceptor-donor atoms, which meet H-bond criteria

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute H-bond acceptor and H-bond donor pairs

    cutoff : float, (default=3.5)
        Distance cutoff for A-D pairs

    tolerance : int, (default=30)
        Range (+/- tolerance) from perfect direction defined by acceptor/donor hybridization
        in which H-bonds are considered as strict.

    Returns
    -------
    a, d : atom_dict-type numpy array
        Aligned arrays of atoms forming H-bond, firstly acceptors,
        secondly donors.

    strict : numpy array, dtype=bool
        Boolean array align with atom pairs, informing whether atoms
        form 'strict' H-bond (pass all angular cutoffs). If false,
        only distance cutoff is met, therefore the bond is 'crude'.
    """
    a, d = close_contacts(mol1.atom_dict[mol1.atom_dict['isacceptor']],
                          mol2.atom_dict[mol2.atom_dict['isdonor']],
                          cutoff)
    # skip empty values
    if len(a) > 0 and len(d) > 0:
        angle1 = angle(d['coords'][:, np.newaxis, :],
                       a['coords'][:, np.newaxis, :],
                       a['neighbors'])
        angle2 = angle(a['coords'][:, np.newaxis, :],
                       d['coords'][:, np.newaxis, :],
                       d['neighbors'])
        strict = (_check_angles(angle1, a['hybridization'], tolerance) &
                  _check_angles(angle2, d['hybridization'], tolerance))
        return a, d, strict
    else:
        return a, d, np.array([], dtype=bool)


def hbonds(mol1, mol2, cutoff=3.5, tolerance=30):
    """Calculates H-bonds between molecules

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute H-bond acceptor and H-bond donor pairs

    cutoff : float, (default=3.5)
        Distance cutoff for A-D pairs

    tolerance : int, (default=30)
        Range (+/- tolerance) from perfect direction defined by atoms hybridization
        in which H-bonds are considered as strict.

    Returns
    -------
    mol1_atoms, mol2_atoms : atom_dict-type numpy array
        Aligned arrays of atoms forming H-bond

    strict : numpy array, dtype=bool
        Boolean array align with atom pairs, informing whether atoms
        form 'strict' H-bond (pass all angular cutoffs). If false,
        only distance cutoff is met, therefore the bond is 'crude'.
    """
    a1, d1, s1 = hbond_acceptor_donor(mol1, mol2, cutoff=cutoff, tolerance=tolerance)
    a2, d2, s2 = hbond_acceptor_donor(mol2, mol1, cutoff=cutoff, tolerance=tolerance)
    return np.concatenate((a1, d2)), np.concatenate((d1, a2)), np.concatenate((s1, s2))


def halogenbond_acceptor_halogen(mol1,
                                 mol2,
                                 tolerance=30,
                                 cutoff=4):
    """Returns pairs of acceptor-halogen atoms, which meet halogen bond criteria

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute halogen bond acceptor and halogen pairs

    cutoff : float, (default=4)
        Distance cutoff for A-H pairs

    tolerance : int, (default=30)
        Range (+/- tolerance) from perfect direction defined by atoms hybridization
        in which halogen bonds are considered as strict.

    Returns
    -------
    a, h : atom_dict-type numpy array
        Aligned arrays of atoms forming halogen bond, firstly acceptors,
        secondly halogens

    strict : numpy array, dtype=bool
        Boolean array align with atom pairs, informing whether atoms
        form 'strict' halogen bond (pass all angular cutoffs). If false,
        only distance cutoff is met, therefore the bond is 'crude'.
    """
    a, h = close_contacts(mol1.atom_dict[mol1.atom_dict['isacceptor']],
                          mol2.atom_dict[mol2.atom_dict['ishalogen']],
                          cutoff)
    # skip empty values
    if len(a) > 0 and len(h) > 0:
        angle1 = angle(h['coords'][:, np.newaxis, :],
                       a['coords'][:, np.newaxis, :],
                       a['neighbors'])
        angle2 = angle(a['coords'][:, np.newaxis, :],
                       h['coords'][:, np.newaxis, :],
                       h['neighbors'])
        strict = (_check_angles(angle1, a['hybridization'], tolerance) &
                  _check_angles(angle2, h['hybridization'], tolerance))
        return a, h, strict
    else:
        return a, h, np.array([], dtype=bool)


def halogenbonds(mol1, mol2, cutoff=4, tolerance=30):
    """Calculates halogen bonds between molecules

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute halogen bond acceptor and halogen pairs

    cutoff : float, (default=4)
        Distance cutoff for A-H pairs

    tolerance : int, (default=30)
        Range (+/- tolerance) from perfect direction defined by atoms hybridization
        in which halogen bonds are considered as strict.

    Returns
    -------
    mol1_atoms, mol2_atoms : atom_dict-type numpy array
        Aligned arrays of atoms forming halogen bond

    strict : numpy array, dtype=bool
        Boolean array align with atom pairs, informing whether atoms
        form 'strict' halogen bond (pass all angular cutoffs). If false,
        only distance cutoff is met, therefore the bond is 'crude'.
    """
    a1, h1, s1 = halogenbond_acceptor_halogen(mol1, mol2, cutoff=cutoff, tolerance=tolerance)
    a2, h2, s2 = halogenbond_acceptor_halogen(mol2, mol1, cutoff=cutoff, tolerance=tolerance)
    return np.concatenate((a1, h2)), np.concatenate((h1, a2)), np.concatenate((s1, s2))


def pi_stacking(mol1, mol2, cutoff=5, tolerance=30):
    """Returns pairs of rings, which meet pi stacking criteria

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute ring pairs

    cutoff : float, (default=5)
        Distance cutoff for Pi-stacking pairs

    tolerance : int, (default=30)
        Range (+/- tolerance) from perfect direction (parallel or
        perpendicular) in which pi-stackings are considered as strict.

    Returns
    -------
    r1, r2 : ring_dict-type numpy array
        Aligned arrays of rings forming pi-stacking

    strict_parallel : numpy array, dtype=bool
        Boolean array align with ring pairs, informing whether rings
        form 'strict' parallel pi-stacking. If false, only distance cutoff is met,
        therefore the stacking is 'crude'.

    strict_perpendicular : numpy array, dtype=bool
        Boolean array align with ring pairs, informing whether rings
        form 'strict' perpendicular pi-stacking (T-shaped, T-face, etc.).
        If false, only distance cutoff is met, therefore the stacking is 'crude'.
    """
    r1, r2 = close_contacts(mol1.ring_dict,
                            mol2.ring_dict,
                            cutoff,
                            x_column='centroid',
                            y_column='centroid')
    if len(r1) > 0 and len(r2) > 0:
        angle1 = angle_2v(r1['vector'], r2['vector'])
        angle2 = angle(r1['vector'] + r1['centroid'],
                       r1['centroid'],
                       r2['centroid'])
        strict_parallel = (((angle1 > 180 - tolerance) | (angle1 < tolerance)) &
                           ((angle2 > 180 - tolerance) | (angle2 < tolerance)))
        strict_perpendicular = (((angle1 > 90 - tolerance) & (angle1 < 90 + tolerance)) &
                                ((angle2 > 180 - tolerance) | (angle2 < tolerance)))
        return r1, r2, strict_parallel, strict_perpendicular
    else:
        return r1, r2, np.array([], dtype=bool), np.array([], dtype=bool)


def salt_bridge_plus_minus(mol1, mol2, cutoff=4):
    """Returns pairs of plus-mins atoms, which meet salt bridge criteria

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute plus and minus pairs

    cutoff : float, (default=4)
        Distance cutoff for A-H pairs

    Returns
    -------
    plus, minus : atom_dict-type numpy array
        Aligned arrays of atoms forming salt bridge, firstly plus, secondly minus

    """
    m1_plus, m2_minus = close_contacts(mol1.atom_dict[mol1.atom_dict['isplus']],
                                       mol2.atom_dict[mol2.atom_dict['isminus']],
                                       cutoff)
    return m1_plus, m2_minus


def salt_bridges(mol1, mol2, *args, **kwargs):
    """Calculates salt bridges between molecules

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute plus and minus pairs

    cutoff : float, (default=4)
        Distance cutoff for plus-minus pairs

    Returns
    -------
    mol1_atoms, mol2_atoms : atom_dict-type numpy array
        Aligned arrays of atoms forming salt bridges
    """
    m1_plus, m2_minus = salt_bridge_plus_minus(mol1, mol2, *args, **kwargs)
    m2_plus, m1_minus = salt_bridge_plus_minus(mol2, mol1, *args, **kwargs)
    return np.concatenate((m1_plus, m1_minus)), np.concatenate((m2_minus, m2_plus))


def hydrophobic_contacts(mol1, mol2, cutoff=4):
    """Calculates hydrophobic contacts between molecules

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute hydrophobe pairs

    cutoff : float, (default=4)
        Distance cutoff for hydrophobe pairs

    Returns
    -------
    mol1_atoms, mol2_atoms : atom_dict-type numpy array
        Aligned arrays of atoms forming hydrophobic contacts

    """
    h1, h2 = close_contacts(mol1.atom_dict[mol1.atom_dict['ishydrophobe']],
                            mol2.atom_dict[mol2.atom_dict['ishydrophobe']],
                            cutoff)
    return h1, h2


def pi_cation(mol1, mol2, cutoff=5, tolerance=30):
    """Returns pairs of ring-cation atoms, which meet pi-cation criteria

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute ring-cation pairs

    cutoff : float, (default=5)
        Distance cutoff for Pi-cation pairs

    tolerance : int, (default=30)
        Range (+/- tolerance) from perfect direction (perpendicular)
        in which pi-cation are considered as strict.

    Returns
    -------
    r1 : ring_dict-type numpy array
        Aligned rings forming pi-stacking

    plus2 : atom_dict-type numpy array
        Aligned cations forming pi-cation

    strict_parallel : numpy array, dtype=bool
        Boolean array align with ring-cation pairs, informing whether
        they form 'strict' pi-cation. If false, only distance cutoff is met,
        therefore the interaction is 'crude'.

    """
    r1, plus2 = close_contacts(mol1.ring_dict,
                               mol2.atom_dict[mol2.atom_dict['isplus']],
                               cutoff,
                               x_column='centroid')
    if len(r1) > 0 and len(plus2) > 0:
        angle1 = angle_2v(r1['vector'], plus2['coords'] - r1['centroid'])
        strict = (angle1 > 180 - tolerance) | (angle1 < tolerance)
        return r1, plus2, strict
    else:
        return r1, plus2, np.array([], dtype=bool)


def acceptor_metal(mol1, mol2, tolerance=30, cutoff=4):
    """Returns pairs of acceptor-metal atoms, which meet metal coordination criteria
    Note: This function is directional (mol1 holds acceptors, mol2 holds metals)

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute acceptor and metal pairs

    cutoff : float, (default=4)
        Distance cutoff for A-M pairs

    tolerance : int, (default=30)
        Range (+/- tolerance) from perfect direction defined by atoms hybridization
        in metal coordination are considered as strict.

    Returns
    -------
    a, d : atom_dict-type numpy array
        Aligned arrays of atoms forming metal coordination,
        firstly acceptors, secondly metals.

    strict : numpy array, dtype=bool
        Boolean array align with atom pairs, informing whether atoms
        form 'strict' metal coordination (pass all angular cutoffs).
        If false, only distance cutoff is met, therefore the interaction
        is 'crude'.
    """
    a, m = close_contacts(mol1.atom_dict[mol1.atom_dict['isacceptor']],
                          mol2.atom_dict[mol2.atom_dict['ismetal']],
                          cutoff)
    # skip empty values
    if len(a) > 0 and len(m) > 0:
        angle1 = angle(m['coords'][:, np.newaxis, :],
                       a['coords'][:, np.newaxis, :],
                       a['neighbors'])
        strict = _check_angles(angle1, a['hybridization'], tolerance)
        return a, m, strict
    else:
        return a, m, np.array([], dtype=bool)


def pi_metal(mol1, mol2, cutoff=5, tolerance=30):
    """Returns pairs of ring-metal atoms, which meet pi-metal criteria

    Parameters
    ----------
    mol1, mol2 : oddt.toolkit.Molecule object
        Molecules to compute ring-metal pairs

    cutoff : float, (default=5)
        Distance cutoff for Pi-metal pairs

    tolerance : int, (default=30)
        Range (+/- tolerance) from perfect direction (perpendicular)
        in which pi-metal are considered as strict.

    Returns
    -------
    r1 : ring_dict-type numpy array
        Aligned rings forming pi-metal

    m : atom_dict-type numpy array
        Aligned metals forming pi-metal

    strict_parallel : numpy array, dtype=bool
        Boolean array align with ring-metal pairs, informing whether
        they form 'strict' pi-metal. If false, only distance cutoff is met,
        therefore the interaction is 'crude'.

    """
    r1, m = close_contacts(mol1.ring_dict,
                           mol2.atom_dict[mol2.atom_dict['ismetal']],
                           cutoff,
                           x_column='centroid')
    if len(r1) > 0 and len(m) > 0:
        angle1 = angle_2v(r1['vector'], m['coords'] - r1['centroid'])
        strict = (angle1 > 180 - tolerance) | (angle1 < tolerance)
        return r1, m, strict
    else:
        return r1, m, np.array([], dtype=bool)
