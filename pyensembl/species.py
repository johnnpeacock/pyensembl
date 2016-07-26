# Copyright (c) 2015-2016. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function, absolute_import, division

from serializable import Serializable

from .ensembl_release_versions import MAX_ENSEMBL_RELEASE

class Species(Serializable):
    """
    Container for combined information about a species name, its synonyn names
    and which reference to use for this species in each Ensembl release.
    """

    # as species instances get created, they get registered in these
    # dictionaries
    _latin_names_to_species = {}
    _common_names_to_species = {}
    _reference_names_to_species = {}

    @classmethod
    def register(cls, latin_name, synonyms, reference_assemblies):
        """
        Create a Species object from the given arguments and enter into
        all the dicts used to look the species up by its fields.
        """
        species = Species(
            latin_name=latin_name,
            synonyms=synonyms,
            reference_assemblies=reference_assemblies)
        cls._latin_names_to_species[species.latin_name] = species
        for synonym in synonyms:
            if synonym in cls._common_names_to_species:
                raise ValueError("Can't use synonym '%s' for both %s and %s" % (
                    synonym,
                    species,
                    cls._common_names_to_species[synonym]))
            cls._common_names_to_species[synonym] = species
        for reference_name in reference_assemblies:
            if reference_name in cls._reference_names_to_species:
                raise ValueError("Can't use reference '%s' for both %s and %s" % (
                    reference_name,
                    species,
                    cls._reference_names_to_species[reference_name]))
            cls._reference_names_to_species[reference_name] = species
        return species

    def __init__(self, latin_name, synonyms=[], reference_assemblies={}):
        """
        Parameters
        ----------
        latin_name : str

        synonyms : list of strings

        reference_assemblies : dict
            Mapping of names of reference genomes onto inclusive ranges of
            Ensembl releases Example: {"GRCh37": (54, 75)}
        """
        self.latin_name = latin_name.lower().replace(" ", "_")
        self.synonyms = synonyms
        self.reference_assemblies = reference_assemblies
        self._release_to_genome = {}
        for (genome_name, (start, end)) in self.reference_assemblies.items():
            for i in range(start, end + 1):
                assert i not in self._release_to_genome, \
                    "Ensembl release %d already has an associated genome"
                self._release_to_genome[i] = genome_name

    def which_reference(self, ensembl_release):
        if ensembl_release not in self._release_to_genome:
            raise ValueError("No genome for %s in Ensembl release %d" % (
                self.latin_name, ensembl_release))
        return self._release_to_genome[ensembl_release]

    def __str__(self):
        return (
            "Species(latin_name='%s', synonyms=%s, reference_assemblies=%s)" % (
                self.latin_name, self.synonyms, self.reference_assemblies))

    def __eq__(self, other):
        return (
            other.__class__ is Species and
            self.latin_name == other.latin_name and
            self.synonyms == other.synonyms and
            self.reference_assemblies == other.reference_assemblies)

    def to_dict(self):
        return {"latin_name": self.latin_name}

    @classmethod
    def from_dict(cls, state_dict):
        return cls._latin_names_to_species[state_dict["latin_name"]]

    def __hash__(self):
        return hash((self.latin_name,
                     tuple(self.synonyms),
                     frozenset(self.reference_assemblies.items())))


def normalize_species_name(name):
    """
    If species name was "Homo sapiens" then replace spaces with underscores
    and return "homo_sapiens". Also replace common names like "human" with
    "homo_sapiens".
    """
    lower_name = name.lower().strip()

    # if given a common name such as "human", look up its latin equivalent
    if lower_name in Species._common_names_to_species:
        return Species._common_names_to_species[lower_name].latin_name

    return lower_name.replace(" ", "_")

def normalize_reference_name(name):
    """
    Search the dictionary of species-specific references to find a reference
    name that matches aside from capitalization.

    If no matching reference is found, raise an exception.
    """
    lower_name = name.strip().lower()
    for reference in Species._reference_names_to_species.keys():
        if reference.lower() == lower_name:
            return reference
    raise ValueError("Reference genome '%s' not found" % name)

def find_species_by_name(species_name):
    latin_name = normalize_species_name(species_name)
    if latin_name not in Species._latin_names_to_species:
        raise ValueError("Species not found: %s" % species_name)
    return Species._latin_names_to_species[latin_name]

def find_species_by_reference(reference_name):
    return Species._reference_names_to_species[normalize_reference_name(reference_name)]

def which_reference(species_name, ensembl_release):
    return find_species_by_name(species_name).which_reference(ensembl_release)

def max_ensembl_release(reference_name):
    species = find_species_by_reference(reference_name)
    (_, max_release) = species.reference_assemblies[reference_name]
    return max_release

def check_species_object(species_name_or_object):
    """
    Helper for validating user supplied species names or objects.
    """
    if isinstance(species_name_or_object, Species):
        return species_name_or_object
    elif isinstance(species_name_or_object, str):
        return find_species_by_name(species_name_or_object)
    else:
        raise ValueError("Unexpected type for species: %s : %s" % (
            species_name_or_object, type(species_name_or_object)))

human = Species.register(
    latin_name="homo_sapiens",
    synonyms=["human"],
    reference_assemblies={
        "GRCh38": (76, MAX_ENSEMBL_RELEASE),
        "GRCh37": (55, 75),
        "NCBI36": (54, 54),
    })

mouse = Species.register(
    latin_name="mus_musculus",
    synonyms=["mouse", "house mouse"],
    reference_assemblies={
        "NCBIM37": (54, 67),
        "GRCm38": (68, MAX_ENSEMBL_RELEASE),

    })
