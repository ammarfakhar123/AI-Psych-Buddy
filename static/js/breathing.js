// Visual breathing timer: Inhale -> Hold -> Exhale -> Hold, repeated.
(function () {
  var circle = document.getElementById('circle');
  var label = document.getElementById('phaseLabel');
  var countdown = document.getElementById('countdown');
  var roundInfo = document.getElementById('roundInfo');
  var startBtn = document.getElementById('startBtn');
  var stopBtn = document.getElementById('stopBtn');
  var patternSel = document.getElementById('pattern');
  var roundsSel = document.getElementById('rounds');
  var timer = null;
  var MIN_SCALE = 1, MAX_SCALE = 2;

  function setScale(scale, seconds) {
    circle.style.transitionDuration = seconds + 's';
    circle.style.transform = 'scale(' + scale + ')';
  }

  function reset(message) {
    clearInterval(timer); timer = null;
    setScale(MIN_SCALE, 0.6);
    label.textContent = message || 'Ready';
    countdown.innerHTML = '&nbsp;';
    startBtn.classList.remove('d-none'); stopBtn.classList.add('d-none');
    patternSel.disabled = false; roundsSel.disabled = false;
  }

  function start() {
    var p = patternSel.value.split(',').map(Number); // inhale, hold, exhale, hold
    var phases = [
      { name: 'Inhale', secs: p[0], scale: MAX_SCALE },
      { name: 'Hold', secs: p[1], scale: MAX_SCALE },
      { name: 'Exhale', secs: p[2], scale: MIN_SCALE },
      { name: 'Hold', secs: p[3], scale: MIN_SCALE }
    ].filter(function (ph) { return ph.secs > 0; });
    var totalRounds = parseInt(roundsSel.value, 10);
    var round = 1, phaseIdx = 0, remaining = 0;

    startBtn.classList.add('d-none'); stopBtn.classList.remove('d-none');
    patternSel.disabled = true; roundsSel.disabled = true;

    function beginPhase() {
      var ph = phases[phaseIdx];
      remaining = ph.secs;
      label.textContent = ph.name;
      countdown.textContent = remaining;
      roundInfo.textContent = 'Round ' + round + ' of ' + totalRounds;
      setScale(ph.scale, ph.secs);
    }

    beginPhase();
    timer = setInterval(function () {
      remaining -= 1;
      if (remaining > 0) { countdown.textContent = remaining; return; }
      phaseIdx += 1;
      if (phaseIdx >= phases.length) {
        phaseIdx = 0; round += 1;
        if (round > totalRounds) { reset('Well done'); roundInfo.textContent = 'Session complete. Notice how you feel.'; return; }
      }
      beginPhase();
    }, 1000);
  }

  startBtn.addEventListener('click', start);
  stopBtn.addEventListener('click', function () { reset('Ready'); roundInfo.innerHTML = '&nbsp;'; });
})();
