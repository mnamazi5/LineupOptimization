# LineupOptimization  
Due to the winner-take-all structure of most Fanduel contests, it is most beneficial to swing for the fences! I created a python script that generates a lineup to maximize the mean+std of a respective slate. The program scrapes nba-reference.com for the past 10-game performance of available players and uses these stats to formulate a solution.

To make data scraping more efficient I created a csv aggregating every active players' URL. I then merge a day's given slate and  URL database on name. To see how I created the database please see PY file named 'CreatingDatabase'. Thank you!
