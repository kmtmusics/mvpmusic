(function(){
  var player=document.getElementById('player');
  var list=document.getElementById('lyricsList');
  var bpmInput=document.getElementById('bpm');
  function beatToSec(beat,bpm){ return (beat/bpm)*60.0; }
  function secToMMSSCS(sec){ var mm=Math.floor(sec/60), ss=Math.floor(sec%60), cs=Math.floor((sec-Math.floor(sec))*100); return (mm<10?'0'+mm:mm)+':'+(ss<10?'0'+ss:ss)+'.'+(cs<10?'0'+cs:cs); }
  document.getElementById('startMetro').onclick=function(){ Metronome.start(parseFloat(bpmInput.value||'84')); };
  document.getElementById('stopMetro').onclick=function(){ Metronome.stop(); };
  document.getElementById('addLine').onclick=function(){
    var li=document.createElement('li'); li.dataset.id='';
    li.innerHTML='<div contenteditable="true" class="lineText">خط جدید...</div><div>Beat: <input class="beat" value=""></div><div>Time: <span class="timeDisplay"></span></div><button class="setFromAudio">Set from Audio</button><button class="setFromMetro">Set from Metronome</button>';
    list.appendChild(li);
  };
  list.addEventListener('click',function(e){
    if(e.target.className==='setFromAudio'){
      var li=e.target.parentNode, input=li.querySelector('.beat');
      var bpm=parseFloat(bpmInput.value||'84'), time=player.currentTime||0, beat=(time*bpm)/60.0;
      input.value=beat.toFixed(3); var td=li.querySelector('.timeDisplay'); if(td) td.innerText=secToMMSSCS(beatToSec(beat,bpm));
    }
    if(e.target.className==='setFromMetro'){
      var li=e.target.parentNode, input=li.querySelector('.beat'); var beat=Metronome.getBeatCount();
      input.value=beat.toFixed(3); var bpm=parseFloat(bpmInput.value||'84'); var td=li.querySelector('.timeDisplay'); if(td) td.innerText=secToMMSSCS(beatToSec(beat,bpm));
    }
  },false);
  bpmInput.addEventListener('change', function(){
    var bpm=parseFloat(bpmInput.value||'84'), items=list.getElementsByTagName('li');
    for(var i=0;i<items.length;i++){ var beat=parseFloat(items[i].querySelector('.beat').value||'0'); var td=items[i].querySelector('.timeDisplay'); if(td) td.innerText=secToMMSSCS(beatToSec(beat,bpm)); }
    Metronome.setBpm(bpm);
  }, false);
  document.getElementById('saveTimes').onclick=function(){
    var items=list.getElementsByTagName('li'), payload=[];
    for(var i=0;i<items.length;i++){
      var id=items[i].dataset.id, beat=parseFloat(items[i].querySelector('.beat').value||'0'), text=items[i].querySelector('.lineText').innerText;
      payload.push({id:id?parseInt(id):null, beat:beat, text:text});
    }
    var xhr=new XMLHttpRequest(); xhr.open('POST', window.location.pathname + '/save_times');
    xhr.setRequestHeader('Content-Type','application/json;charset=UTF-8');
    xhr.onload=function(){ alert(xhr.status===200?'Saved':'Error'); }; xhr.send(JSON.stringify(payload));
  };
})();
