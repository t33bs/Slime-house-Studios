"""Local animation recipe definitions for the standalone editor."""
TEMPLATES={
 'Idle / Breathing':['Neutral','Inhale','Hold','Exhale'],
 'Walking':['Contact left','Down','Passing left','Contact right','Down','Passing right'],
 'Sleeping':['Lie down','Eyes close','Slow inhale','Slow exhale'],
 'Eating':['Look at food','Open mouth','Bite','Chew','Swallow','Reset'],
 'Happy / Celebrating':['Ready','Crouch','Jump','Peak','Land','Reset'],
 'Grooming':['Sit','Raise paw','Lick paw','Wipe face','Wipe face again','Lower paw','Blink','Reset'],
 'Flying / Hovering':['Wings up','Mid down','Wings down','Glide','Mid up','Wings up'],
 'Custom':['Start','Middle','End'],
}
REQUIRED={'Walking':['Body','Legs / paws'],'Flying / Hovering':['Body','Wings'],'Eating':['Head','Mouth']}
