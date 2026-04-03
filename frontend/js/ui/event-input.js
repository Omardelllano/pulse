/**
 * EventInput: Text field + submit for user event simulation (P1).
 * P0: wired up but submit just logs to console.
 */
class EventInput {
  constructor(form, onSubmit) {
    this.form     = form;
    this.onSubmit = onSubmit;
    if (!form) return;
    form.addEventListener('submit', e => {
      e.preventDefault();
      const input = form.querySelector('input[type="text"]');
      const text  = (input && input.value.trim()) || '';
      if (text.length >= 3) {
        this.onSubmit(text);
        input.value = '';
      }
    });
  }
}
