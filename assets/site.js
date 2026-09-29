(() => {
  const publicationFilters = document.querySelector('[data-publication-filters]');
  if (publicationFilters) {
    const search = document.querySelector('#publication-search');
    const year = document.querySelector('#publication-year');
    const type = document.querySelector('#publication-type');
    const records = [...document.querySelectorAll('.publication-list > li')];
    const sections = [...document.querySelectorAll('.publication-year')];
    const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const searchable = new Map(records.map(record => [record, normalize(record.textContent)]));
    function applyFilters() {
      const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
      let count = 0;
      records.forEach(record => {
        const matches = (!year.value || record.dataset.year === year.value)
          && (!type.value || record.dataset.type === type.value)
          && words.every(word => searchable.get(record).includes(word));
        record.hidden = !matches;
        if (matches) count++;
      });
      sections.forEach(section => {
        section.hidden = !section.querySelector('li:not([hidden])');
        document.querySelector(`.year-index a[href="#${section.id}"]`).hidden = section.hidden;
      });
      document.querySelectorAll('.publication-group').forEach(group => {
        group.hidden = !group.querySelector('li:not([hidden])');
      });
      document.querySelector('[data-abstract-jump]').hidden = document.querySelector('#conference-abstracts').hidden;
      document.querySelector('#publication-count').textContent = `${count} of ${records.length} research outputs`;
      document.querySelector('#no-publications').hidden = count !== 0;
    }
    search.addEventListener('input', applyFilters);
    year.addEventListener('change', applyFilters);
    type.addEventListener('change', applyFilters);
    document.querySelector('#clear-filters').addEventListener('click', () => {
      search.value = ''; year.value = ''; type.value = ''; applyFilters(); search.focus();
    });
    publicationFilters.hidden = false;
    applyFilters();
  }
  const updateFilters = document.querySelector('[data-update-filters]');
  if (updateFilters) {
    const category = document.querySelector('#update-category');
    const records = [...document.querySelectorAll('.updates-list > li')];
    const filter = () => {
      let count = 0;
      records.forEach(record => {
        record.hidden = Boolean(category.value && record.dataset.category !== category.value);
        if (!record.hidden) count++;
      });
      document.querySelector('#update-count').textContent = `${count} news ${count === 1 ? 'item' : 'items'}`;
    };
    category.addEventListener('change', filter);
    updateFilters.hidden = false;
    filter();
  }
})();
