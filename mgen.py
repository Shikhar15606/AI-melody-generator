# for writing cli
import click
from datetime import datetime
from typing import List, Dict
# to generate mid files
from midiutil import MIDIFile
# library to generate sound
from pyo import *
# importing our genetic algorithm
from algorithms.genetic import generate_genome, Genome, selection_pair, single_point_crossover, mutation
 
BITS_PER_NOTE = 4
# list of options for the keys and scales input
KEYS = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"]
SCALES = ["major", "minorM", "dorian", "phrygian", "lydian", "mixolydian", "majorBlues", "minorBlues"]
 
 
def int_from_bits(bits: List[int]) -> int:
   return int(sum([bit*pow(2, index) for index, bit in enumerate(bits)]))
 
# this function takes genome and returns a melody
def genome_to_melody(genome: Genome, num_bars: int, num_notes: int, num_steps: int,
                    pauses: int, key: str, scale: str, root: int) -> Dict[str, list]:
   notes = [genome[i * BITS_PER_NOTE:i * BITS_PER_NOTE + BITS_PER_NOTE] for i in range(num_bars * num_notes)]
 
   note_length = 4 / float(num_notes)
 
   scl = EventScale(root=key, scale=scale, first=root)
 
   melody = {
       "notes": [],
       "velocity": [],
       "beat": []
   }
 
   for note in notes:
       integer = int_from_bits(note)
 
       if not pauses:
           integer = int(integer % pow(2, BITS_PER_NOTE - 1))
 
       if integer >= pow(2, BITS_PER_NOTE - 1):
           melody["notes"] += [0]
           melody["velocity"] += [0]
           melody["beat"] += [note_length]
       else:
           if len(melody["notes"]) > 0 and melody["notes"][-1] == integer:
               melody["beat"][-1] += note_length
           else:
               melody["notes"] += [integer]
               melody["velocity"] += [127]
               melody["beat"] += [note_length]
 
   steps = []
   for step in range(num_steps):
       steps.append([scl[(note+step*2) % len(scl)] for note in melody["notes"]])
 
   melody["notes"] = steps
   return melody
 
# uses the previous function to generate melody from genome and then
# returns an event which will be given to the pyo server
# and get the sound from pyo server
def genome_to_events(genome: Genome, num_bars: int, num_notes: int, num_steps: int,
                    pauses: bool, key: str, scale: str, root: int, bpm: int) -> [Events]:
   melody = genome_to_melody(genome, num_bars, num_notes, num_steps, pauses, key, scale, root)
 
   return [
       Events(
           midinote=EventSeq(step, occurrences=1),
           midivel=EventSeq(melody["velocity"], occurrences=1),
           beat=EventSeq(melody["beat"], occurrences=1),
           attack=0.001,
           decay=0.05,
           sustain=0.5,
           release=0.005,
           bpm=bpm
       ) for step in melody["notes"]
   ]
 
# the function to calculate the fitness of a value
def fitness(genome: Genome, s: Server, num_bars: int, num_notes: int, num_steps: int,
           pauses: bool, key: str, scale: str, root: int, bpm: int) -> int:
   m = metronome(bpm)
# generating music events from our genome
   events = genome_to_events(genome, num_bars, num_notes, num_steps, pauses, key, scale, root, bpm)
# playing the music
   for e in events:
       e.play()
   s.start()
# getting the melody rating from user
   rating = input("Rating (0-5)")
# after entering rating stop playing the music
   for e in events:
       e.stop()
   s.stop()
# wait for 1 second
   time.sleep(1)
# if rating is not an integer then throw error
   try:
       rating = int(rating)
   except ValueError:
       rating = 0
# return rating which will be used as fitness value
   return rating
 
 
def metronome(bpm: int):
   met = Metro(time=1 / (bpm / 60.0)).play()
   t = CosTable([(0, 0), (50, 1), (200, .3), (500, 0)])
   amp = TrigEnv(met, table=t, dur=.25, mul=1)
   freq = Iter(met, choice=[660, 440, 440, 440])
   return Sine(freq=freq, mul=amp).mix(2).out()
 
# saves the melody file as .mid extension in our folder
def save_genome_to_midi(filename: str, genome: Genome, num_bars: int, num_notes: int, num_steps: int,
                       pauses: bool, key: str, scale: str, root: int, bpm: int):
   melody = genome_to_melody(genome, num_bars, num_notes, num_steps, pauses, key, scale, root)
 
   if len(melody["notes"][0]) != len(melody["beat"]) or len(melody["notes"][0]) != len(melody["velocity"]):
       raise ValueError
 
   mf = MIDIFile(1)
 
   track = 0
   channel = 0
 
   time = 0.0
   mf.addTrackName(track, time, "Sample Track")
   mf.addTempo(track, time, bpm)
 
   for i, vel in enumerate(melody["velocity"]):
       if vel > 0:
           for step in melody["notes"]:
               mf.addNote(track, channel, step[i], time, melody["beat"][i], vel)
 
       time += melody["beat"][i]
 
   os.makedirs(os.path.dirname(filename), exist_ok=True)
   with open(filename, "wb") as f:
       mf.writeFile(f)
 
# =============== Input using click library ===================
@click.command()
# 1 bar is 1 unit in music
@click.option("--num-bars", default=8, prompt='Number of bars:', type=int)
# no of notes in 1 bar
@click.option("--num-notes", default=4, prompt='Notes per bar:', type=int)
# how many notes you want to be on top of each other
@click.option("--num-steps", default=1, prompt='Number of steps:', type=int)
# do you want pauses or a continuous melody
@click.option("--pauses", default=True, prompt='Introduce Pauses?', type=bool)
@click.option("--key", default="C", prompt='Key:', type=click.Choice(KEYS, case_sensitive=False))
# some notes which sound good together
@click.option("--scale", default="major", prompt='Scale:', type=click.Choice(SCALES, case_sensitive=False))
# how high should the melody be
@click.option("--root", default=4, prompt='Scale Root:', type=int)
# what should be the population size(no of melodies)
@click.option("--population-size", default=10, prompt='Population size:', type=int)
# how many mutations you want in each generation
@click.option("--num-mutations", default=2, prompt='Number of mutations:', type=int)
# the probability of mutation
@click.option("--mutation-probability", default=0.5, prompt='Mutations probability:', type=float)
@click.option("--bpm", default=128, type=int)
# ================== Input Finished ==========================
 
# defining our main function
def main(num_bars: int, num_notes: int, num_steps: int, pauses: bool, key: str, scale: str, root: int,
        population_size: int, num_mutations: int, mutation_probability: float, bpm: int):
# the folder name is the current timestamp
   folder = str(int(datetime.now().timestamp()))
# generating a random population of genome where each genome has same length
# the no of genome in the population will be same as that of given population size
   population = [generate_genome(num_bars * num_notes * BITS_PER_NOTE) for _ in range(population_size)]
# will be used for starting and stopping the pyo server
   s = Server().boot()
# the first population with id 0
   population_id = 0
# loop until user says no
   running = True
   while running:
# randomly shuffling the generated population
       random.shuffle(population)
# for every genome in population make a tuple with the genome and its fitness value
       population_fitness = [(genome, fitness(genome, s, num_bars, num_notes, num_steps, pauses, key, scale, root, bpm)) for genome in population]
# sort all the genomes in population in decreasing order of their fitness
       sorted_population_fitness = sorted(population_fitness, key=lambda e: e[1], reverse=True)
# from the sorted list just extract the genomes and leave the fitness value
       population = [e[0] for e in sorted_population_fitness]
# taking the two best genomes as it is in the next generation
       next_generation = population[0:2]
 
       for j in range(int(len(population) / 2) - 1):
# take the genome and return its fitness value
           def fitness_lookup(genome):
               for e in population_fitness:
                   if e[0] == genome:
                       return e[1]
               return 0
# selecting 2 parents from population
           parents = selection_pair(population, fitness_lookup)
# generating 2 offspring from the 2 parents by single crossover
           offspring_a, offspring_b = single_point_crossover(parents[0], parents[1])
# mutating the 2 offsprings
           offspring_a = mutation(offspring_a, num=num_mutations, probability=mutation_probability)
           offspring_b = mutation(offspring_b, num=num_mutations, probability=mutation_probability)
# adding the offsprings to the next generation
           next_generation += [offspring_a, offspring_b]
# printing our current population id
       print(f"population {population_id} done")
# generating music events from our most fit genome
       events = genome_to_events(population[0], num_bars, num_notes, num_steps, pauses, key, scale, root, bpm)
# playing the music
       for e in events:
           e.play()
       s.start()
# play music until some input is given
       input("here is the no1 hit …")
# stop music after entering the input
       s.stop()
       for e in events:
           e.stop()
# wait for 1 second
       time.sleep(1)
# start playing the second best music
       events = genome_to_events(population[1], num_bars, num_notes, num_steps, pauses, key, scale, root, bpm)
       for e in events:
           e.play()
       s.start()
       input("here is the second best …")
       s.stop()
       for e in events:
           e.stop()
# wait for a second
       time.sleep(1)
# saving all the population mid file in the folder name given above
       print("saving population midi …")
       for i, genome in enumerate(population):
           save_genome_to_midi(f"{folder}/{population_id}/{scale}-{key}-{i}.mid", genome, num_bars, num_notes, num_steps, pauses, key, scale, root, bpm)
       print("done")
# if yes then more population generations will be generated if no then end of program
       running = input("continue? [Y/n]") != "n"
       population = next_generation
       population_id += 1
 
# calling our main function
if __name__ == '__main__':
   main()