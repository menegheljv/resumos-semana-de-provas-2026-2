/* Comportamento do site: quiz com correção na hora, índice que acompanha a leitura e confete. */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function store(key, value) {
    try {
      if (value === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, value);
    } catch (e) { /* armazenamento indisponível: o site funciona sem */ }
    return null;
  }

  function celebrate() {
    if (reduceMotion) return;
    var colors = ["#e85d9e", "#b79dfb", "#7db4f2", "#63b58a", "#f3c969"];
    for (var i = 0; i < 90; i++) {
      var p = document.createElement("span");
      p.className = "confetti-piece";
      p.style.left = Math.random() * 100 + "vw";
      p.style.backgroundColor = colors[i % colors.length];
      p.style.setProperty("--drift", Math.random() * 240 - 120 + "px");
      p.style.animationDelay = Math.random() * 0.35 + "s";
      document.body.appendChild(p);
      (function (el) { setTimeout(function () { el.remove(); }, 3300); })(p);
    }
  }

  /* ---------------------------------------------------------- quiz */
  function initQuiz(root) {
    var slug = root.getAttribute("data-quiz");
    var questions = Array.prototype.slice.call(root.querySelectorAll(".question"));
    var total = questions.length;
    var wrap = root.closest("main");
    var elAnswered = wrap.querySelector("[data-answered]");
    var elCorrect = wrap.querySelector("[data-correct]");
    var elProgress = wrap.querySelector("[data-progress]");
    var result = wrap.querySelector("[data-result]");
    var firstWrongBtn = wrap.querySelector("[data-first-wrong]");
    var best = store("p4n-best-" + slug);

    function counts() {
      var answered = 0, correct = 0;
      questions.forEach(function (q) {
        if (q.classList.contains("done")) {
          answered++;
          if (q.classList.contains("is-right")) correct++;
        }
      });
      return { answered: answered, correct: correct };
    }

    function refresh(showResult) {
      var c = counts();
      elAnswered.textContent = c.answered;
      elCorrect.textContent = c.correct;
      elProgress.style.width = (c.answered / total) * 100 + "%";
      if (c.answered === total && showResult) finish(c);
    }

    function finish(c) {
      var pct = Math.round((c.correct / total) * 100);
      var title, text;
      if (pct === 100) { title = "Gabaritou. " + c.correct + " de " + total + "."; text = "Sem erro nenhum. Agora é só não esquecer o que você acabou de acertar."; }
      else if (pct >= 70) { title = c.correct + " de " + total + " (" + pct + "%)."; text = "Bom resultado. Refaça só o que errou e volte ao resumo nos pontos marcados como \"Cai na prova\"."; }
      else { title = c.correct + " de " + total + " (" + pct + "%)."; text = "Ainda dá tempo. Releia o resumo, faça o quiz de novo e dessa vez leia cada explicação."; }
      var prev = parseInt(best || "0", 10);
      if (!best || c.correct > prev) {
        store("p4n-best-" + slug, String(c.correct));
        best = String(c.correct);
        if (prev && c.correct > prev) text += " Novo recorde: antes eram " + prev + ".";
      } else if (prev) {
        text += " Seu melhor até agora: " + prev + ".";
      }
      result.querySelector("[data-result-title]").textContent = title;
      result.querySelector("[data-result-text]").textContent = text;
      firstWrongBtn.hidden = c.correct === total;
      result.hidden = false;
      result.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
      if (pct === 100) celebrate();
    }

    root.addEventListener("click", function (event) {
      var btn = event.target.closest(".option");
      if (!btn || btn.disabled) return;
      var q = btn.closest(".question");
      var answer = q.getAttribute("data-answer");
      var chosen = btn.getAttribute("data-key");
      q.classList.add("done");
      q.classList.add(chosen === answer ? "is-right" : "is-wrong");
      q.querySelectorAll(".option").forEach(function (o) {
        o.disabled = true;
        var key = o.getAttribute("data-key");
        if (key === answer) o.classList.add("correct");
        else if (key === chosen) o.classList.add("wrong");
      });
      q.querySelector(".explain").hidden = false;
      refresh(true);
    });

    function reset() {
      questions.forEach(function (q) {
        q.classList.remove("done", "is-right", "is-wrong");
        q.querySelectorAll(".option").forEach(function (o) {
          o.disabled = false;
          o.classList.remove("correct", "wrong");
        });
        q.querySelector(".explain").hidden = true;
      });
      result.hidden = true;
      refresh(false);
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    }

    wrap.querySelectorAll("[data-reset]").forEach(function (b) { b.addEventListener("click", reset); });
    firstWrongBtn.addEventListener("click", function () {
      var wrong = root.querySelector(".question.is-wrong");
      if (wrong) wrong.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
    });
    refresh(false);
  }

  /* ---------------------------------------------------------- índice da matéria */
  function initToc() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
    if (!links.length) return;
    var items = links.map(function (a) {
      return { link: a, el: document.getElementById(a.getAttribute("href").slice(1)) };
    }).filter(function (item) { return item.el; });
    var current = null, ticking = false;

    function update() {
      ticking = false;
      var line = window.innerHeight * 0.3;
      var active = null;
      items.forEach(function (item) {
        if (item.el.getBoundingClientRect().top <= line) active = item;
      });
      if (active && active.link === current) return;
      if (current) current.classList.remove("active");
      current = active ? active.link : null;
      if (current) current.classList.add("active");
    }

    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    update();
    // no celular o índice começa fechado, no desktop fica aberto
    var details = document.querySelector(".toc details");
    if (details && window.matchMedia("(max-width: 959px)").matches) details.removeAttribute("open");
  }

  document.addEventListener("DOMContentLoaded", function () {
    var quiz = document.querySelector(".quiz");
    if (quiz) initQuiz(quiz);
    initToc();
  });
})();
