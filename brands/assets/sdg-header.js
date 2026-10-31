'use strict';
(() => {
  const goals = [{"id":1,"name":"消除貧窮","related":false,"summary":"消除各地一切形式的貧窮。","url":"https://sdgs.un.org/goals/goal1"},{"id":2,"name":"消除飢餓","related":false,"summary":"消除飢餓，促進糧食安全、營養改善與永續農業。","url":"https://sdgs.un.org/goals/goal2"},{"id":3,"name":"健康與福祉","related":false,"summary":"確保健康生活，促進所有年齡層的福祉。","url":"https://sdgs.un.org/goals/goal3"},{"id":4,"name":"優質教育","related":true,"summary":"確保包容、公平的優質教育，促進終身學習。","connection":"論壇以 STEM 教育與青年參與為主題，關注女孩的學習機會。","url":"https://sdgs.un.org/goals/goal4"},{"id":5,"name":"性別平等","related":false,"summary":"實現性別平等，賦權所有婦女與女孩。","url":"https://sdgs.un.org/goals/goal5"},{"id":6,"name":"淨水與衛生","related":false,"summary":"確保所有人享有可用、永續管理的水與衛生設施。","url":"https://sdgs.un.org/goals/goal6"},{"id":7,"name":"可負擔的潔淨能源","related":false,"summary":"確保所有人取得可負擔、可靠、永續的現代能源。","url":"https://sdgs.un.org/goals/goal7"},{"id":8,"name":"尊嚴就業與經濟成長","related":false,"summary":"促進包容、永續的經濟成長與尊嚴就業。","url":"https://sdgs.un.org/goals/goal8"},{"id":9,"name":"產業、創新與基礎建設","related":false,"summary":"建設有韌性的基礎建設，促進永續工業化與創新。","url":"https://sdgs.un.org/goals/goal9"},{"id":10,"name":"減少不平等","related":false,"summary":"減少國家內部與國家之間的不平等。","url":"https://sdgs.un.org/goals/goal10"},{"id":11,"name":"永續城市與社區","related":false,"summary":"建構包容、安全、有韌性且永續的城市與住區。","url":"https://sdgs.un.org/goals/goal11"},{"id":12,"name":"責任消費與生產","related":false,"summary":"確保永續的消費與生產模式。","url":"https://sdgs.un.org/goals/goal12"},{"id":13,"name":"氣候行動","related":false,"summary":"採取緊急行動，對抗氣候變遷及其影響。","url":"https://sdgs.un.org/goals/goal13"},{"id":14,"name":"海洋生態","related":false,"summary":"保育並永續利用海洋與海洋資源。","url":"https://sdgs.un.org/goals/goal14"},{"id":15,"name":"陸域生態","related":false,"summary":"保護陸域生態系，永續管理森林並維護生物多樣性。","url":"https://sdgs.un.org/goals/goal15"},{"id":16,"name":"和平、正義與健全制度","related":false,"summary":"促進和平、包容的社會，建立可問責且包容的制度。","url":"https://sdgs.un.org/goals/goal16"},{"id":17,"name":"夥伴關係","related":true,"summary":"強化執行方法，活化永續發展的全球夥伴關係。","connection":"台美女童軍跨國交流，串連教育、青年與女性權益的合作。","url":"https://sdgs.un.org/goals/goal17"}];
  const navigation = document.querySelector('.sdg-navigation');
  if (!navigation) return;
  const buttons = [...document.querySelectorAll('.sdg-button')];
  const panel = document.getElementById('sdg-detail');
  const closeButton = document.querySelector('.sdg-close');
  let selectedButton = null;
  function closePanel(returnFocus = false) {
    panel.hidden = true;
    buttons.forEach(button => button.setAttribute('aria-expanded', 'false'));
    if (returnFocus && selectedButton) selectedButton.focus({preventScroll: true});
    selectedButton = null;
  }
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => {
      if (selectedButton === button && !panel.hidden) return closePanel();
      const goal = goals.find(item => item.id === Number(button.dataset.goal));
      if (!goal) return;
      const related = button.dataset.related === 'true';
      selectedButton = button;
      buttons.forEach(item => item.setAttribute('aria-expanded', String(item === button)));
      document.getElementById('sdg-detail-title').textContent = `SDG ${goal.id} / ${goal.name}`;
      document.getElementById('sdg-detail-status').textContent = related ? '此頁對應目標' : '此頁未標示此目標';
      document.getElementById('sdg-detail-copy').textContent = related && navigation.dataset.sdgScope === 'girl-scouts' ? goal.connection || goal.summary : goal.summary;
      document.getElementById('sdg-detail-link').href = goal.url;
      panel.hidden = false;
    });
    button.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % buttons.length;
      if (event.key === 'ArrowLeft') next = (index + buttons.length - 1) % buttons.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = buttons.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      buttons[next].focus({preventScroll: true});
      buttons[next].scrollIntoView({block: 'nearest', inline: 'nearest', behavior: 'instant'});
    });
  });
  closeButton.addEventListener('click', () => closePanel(true));
  navigation.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) {
      closePanel(true);
      event.preventDefault();
    }
  });
  panel.setAttribute('aria-live', 'polite');
})();
