# Hello   
[Motivation for this project](https://en.wikipedia.org/wiki/Autism)

# Deps   
cd to the gigaforge simulations dir   
clone this amazing json reading thingy:   
```bash
curl -O https://raw.githubusercontent.com/nlohmann/json/develop/single_include/nlohmann/json.hpp
```
```
pip3 install tabulate
```

# How to
Put this directory in your addon folder    
1. Make sure to have all the dependencies 
2. Open wow and press the button above the character pane to export your characters gear data with the addon.
3. Delete all contents of `items.json` and paste in your characters gear data and save.
4. Edit `stat_prio.json` to fit your stat weights and which stats you want to reach a certain cap
5. run `options.py` This creates every possible permutation of all your items (every reforge, gen and enchaing possibility)
6. run `compute.py` or `./compute`. The compiled c++ computation program is faster. the python script is easier to run.
7. When computing is done, run `results.py`. This prints out the most optimal combination of reforgin, gemming and enchanting
8. Paste the reforging string into the new window that pops up when you go to a reforging vendor

The sockets, enchant and reforge are shown for each item in a intuitive manner, showing you which pieces should have what

Example of a reforge string   
`[{1: 5}, {2: 5}, {3: 5}, {5: 5}, {6: 5}, {7: 5}, {8: 5}, {9: 5}, {10: 11}, {11: 5}, {12: 5}, {13: 3}, {14: 6}, {15: 5}, {16: 5}]`

## how to compile compute.cpp
### with clang
```
clang++ -std=c++17 -O2 -o compute compute.cpp
```
and run `./compute`

### with cl (windows)
```
cl /std:c++17 compute.pp
```
and run `compute.exe`

# How it works (in short)
Takes your characters data and finds every possible combination that can be created out of that item by reforging, adding gems and enchanting it.
Gems are filtered to only pick the best ones according to your stat weights as well as any gem that can contribute to reaching a stat cap. Enchants and reforges are filtered in the same way.   
This IMMENSELY reduces the amount of iterations that are needed to find the best solution.

Some quick maths for a unfiltered item set considering only reforging to show how insanely this scales     
14 items can be reforged and have 2 stats on them( we dont count trinkets in this example and character is dual wielding)   
There are 8 stats that can be reforged into, a stat cannot be reforged into a stat that is already on the item   
- each stat on an item has 6 possible iterations   
- this gives us 12 possible states + the un-reforged state gives us 13   

with 13 posible states per item we get a total of $13^{14}$ ≈ 4 quadrillion (3937 trillion) unique states of one gear set   
With a PC like mine this would take roughly **83 years** at about 1.5 million iterations per second   
With filtering we get it down to somewhere between 1 and 2 minutes (about 29 million times faster)   

For fun lets add gems using the default item setup that comes with this repo
with 63 different gems per socket and 13 different reforge combinations we get for one item with 3 sockets:   
$63 * 63 * 63 * 13 = 3.250.611$ combinations for just that item   
continuing this with the rest of the default item setup   

$$(63^{3} * 13) * (63^{2} * 13) * (63 * 13)^{5} * 13^{6} * 7^2 =1.461723e+34$$   

This means that, if we do no filtering by the time this simulation has finished, the universe would have fizzled out into an endless lightless void where every star has long burned out.
But with filtering, we finish the simulation in roughly 5 to 8 minutes (with my PC as benchmark)
