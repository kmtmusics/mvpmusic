var Metronome = (function(){
  var ctx=null, nextTick=0, scheduleAhead=0.1, isRunning=false;
  var bpm=84, beatCount=0, beatsPerBar=4;
  function init(){ if(!ctx) ctx=new (window.AudioContext||window.webkitAudioContext)(); }
  function clickAt(t,accent){
    var o=ctx.createOscillator(), g=ctx.createGain();
    o.frequency.value = accent? 1200: 800; g.gain.value=0.2;
    o.connect(g); g.connect(ctx.destination); o.start(t); o.stop(t+0.02);
  }
  function scheduler(){
    while(nextTick < ctx.currentTime + scheduleAhead){
      clickAt(nextTick, (beatCount % beatsPerBar)===0);
      var bar = Math.floor(beatCount/beatsPerBar)+1;
      var beat = (beatCount%beatsPerBar)+1;
      var el=document.getElementById('meterState'); if(el) el.innerText='Bar '+bar+' : Beat '+beat;
      beatCount++; nextTick += 60.0 / bpm;
    }
    if(isRunning) requestAnimationFrame(scheduler);
  }
  return {
    start:function(b){ init(); bpm=b||bpm; isRunning=true; nextTick=ctx.currentTime+0.05; scheduler(); },
    stop:function(){ isRunning=false; },
    getBeatCount:function(){ return beatCount; },
    setBeatCount:function(v){ beatCount=v; },
    setBpm:function(v){ bpm=v; }
  };
})();
