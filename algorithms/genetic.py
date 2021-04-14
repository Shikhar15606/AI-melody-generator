from random import choices, randint, randrange, random, sample
from typing import List, Optional, Callable, Tuple

Genome = List[int]
Population = List[Genome]
PopulateFunc = Callable[[], Population]
FitnessFunc = Callable[[Genome], int]
SelectionFunc = Callable[[Population, FitnessFunc], Tuple[Genome, Genome]]
CrossoverFunc = Callable[[Genome, Genome], Tuple[Genome, Genome]]
MutationFunc = Callable[[Genome], Genome]
PrinterFunc = Callable[[Population, int, FitnessFunc], None]


# given the length this function will generate a genome which 
# is a random collection of 0 and 1 and has the given length
def generate_genome(length: int) -> Genome:
    return choices([0, 1], k=length)

# this method generates the population or 
# in other words a list of genomes with given length
def generate_population(size: int, genome_length: int) -> Population:
    return [generate_genome(genome_length) for _ in range(size)]

# this method takes 2 genomes with same length and it randomly 
# breaks the genomes at any point in 2 parts and then 
# cross join them to generate 2 new genomes
def single_point_crossover(a: Genome, b: Genome) -> Tuple[Genome, Genome]:
    if len(a) != len(b):
        raise ValueError("Genomes a and b must be of same length")

    length = len(a)
    if length < 2:
        return a, b

    p = randint(1, length - 1)
    return a[0:p] + b[p:], b[0:p] + a[p:]
# the mutation function takes a genome and with a certain probability changes ones to zeros 
# and zeros to ones at random positions for that we choose a random index 
# and if random returns a value higher than probability we leave it as it is 
# otherwise it is in our mutation probability and we toggle index's value

def mutation(genome: Genome, num: int = 1, probability: float = 0.5) -> Genome:
    for _ in range(num):
        index = randrange(len(genome))
        genome[index] = genome[index] if random() > probability else abs(genome[index] - 1)
    return genome

# function to select 2 genomes from the population 
# genomes with higher fitness are more likely to be chosen 
# as the fitness of a genome acts as its weight. 
# the k parameter states that we draw 2 genomes from our population.

def selection_pair(population: Population, fitness_func: FitnessFunc) -> Population:
    return sample(
        population=generate_weighted_distribution(population, fitness_func),
        k=2
    )

# generates a weighted distribution with the fitness value as weight of a genome
def generate_weighted_distribution(population: Population, fitness_func: FitnessFunc) -> Population:
    result = []

    for gene in population:
        result += [gene] * int(fitness_func(gene)+1)

    return result

# sort all the genomes in population in decreasing order of their fitness
def sort_population(population: Population, fitness_func: FitnessFunc) -> Population:
    return sorted(population, key=fitness_func, reverse=True)


def genome_to_string(genome: Genome) -> str:
    return "".join(map(str, genome))