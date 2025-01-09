new Vue({
  el: '#app',
  delimiters: ['[[', ']]'], // Change delimiters to avoid conflict with Tornado
  data: {
    student_id: '',
    language: '',
    messages: [],
    question: '',
    hint: false,  // whether student explicitely asks for a hint
    editor: null,
    consoleOutput: 'This is your Console. Press "Run Code" to see your output here...',
    consoleError: '',
    loading: false,  // disables the UI while backend is computing the response
  },
  computed: {
    // Computed property to filter only assistant messages
    assistantMessages() {
      return this.messages.filter(msg => msg.role === 'assistant');
    }
  },
  methods: {
    // Method to render Markdown content to sanitized HTML
    renderMarkdown(content) {
      if (!content) return '';
      const rawHtml = marked.parse(content);
      return DOMPurify.sanitize(rawHtml);
    },
    gimmeHint() {
      this.hint = true;
      this.runCode();
    },
    runCode() {
      this.loading = true; // disable buttons & editor
      const code = this.editor.getValue();
      const payload = {
        code: code,
        student_id: this.student_id,
        question: this.question,
        messages: this.messages,
        hint: this.hint,
      };

      // Send data to the backend
      fetch('/api/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        this.updateEditorAndConsole(data.messages);
      })
      .catch(error => {
        console.error('Error:', error);
        this.consoleError = 'Error executing code.';
        this.loading = false;
      });
    },
    // Updates the CodeMirror editor and console output based on the last user message
    updateEditorAndConsole(messages) {
      this.messages = messages;
      if (!messages || !Array.isArray(messages) || messages.length === 0) return;

      const lastUserMessage = messages.slice().reverse().find(msg => msg.role === 'user');
      console.log("lastUserMessage", lastUserMessage);
      if (lastUserMessage && "code" in lastUserMessage) {
        this.editor.setValue(lastUserMessage.code);
        this.consoleOutput = lastUserMessage.consoleOutput || '';
        this.consoleError = lastUserMessage.consoleError || '';
        this.question = ''; // reset question
      }
      this.loading = false;  // show buttons and editors
      this.hint = false;
    },
    // Scroll to the bottom of the chatbot
    scrollToBottom() {
      this.$nextTick(() => {
        const chatbot = this.$el.querySelector('#chatbot');
        chatbot.scrollTop = chatbot.scrollHeight;
      });
    },
    // Retrieve user data from localStorage, else ask to register
    retrieveUserData() {
      const storedId = localStorage.getItem('student_id');
      const storedLanguage = localStorage.getItem('student_language');
      if (storedId && storedLanguage) {
        this.student_id = storedId;
        this.language = storedLanguage;
        this.afterRetrieveUserData();
      } else {
        // Show dialog if data is not present
        this.showDialog();
      }
    },
    // Show the "registration" dialog
    showDialog() {
      const dialog = this.$refs.userDialog;
      if (typeof dialog.showModal === 'function') {
        dialog.showModal();
      } else {
        alert("Sorry, the <dialog> API is not supported by this browser.");
      }
    },
    // When Registration Dialog submitted
    submitUserData() {
      // Basic validation
      if (this.student_id && this.language) {
        // remove anything after the @
        this.student_id = this.student_id.replace(/@.*/, '');
        // Save to localStorage
        localStorage.setItem('student_id', this.student_id);
        localStorage.setItem('student_language', this.language);
        // Close the dialog
        const dialog = this.$refs.userDialog;
        dialog.close();
        this.afterRetrieveUserData();
      } else {
        alert('Please enter both email and language.');
      }
    },
    // whole lot of initialization here below:
    afterRetrieveUserData(){
      // Fetch initial messages from the backend
      this.loading = true; // disable buttons & editor
      fetch('/api/init', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ student_id: this.student_id, language: this.language }),
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Init API error: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("messages afterRetrieveUserData", data.messages);
        if (data.messages && Array.isArray(data.messages)) {
          this.updateEditorAndConsole(data.messages);
        } else {
          console.error('No messages found in init response.');
        }
      })
      .catch(error => {
        console.error('Error initializing messages:', error);
        //this.messages.push({ role: 'assistant', content: 'Failed to load initial messages.' });
      });


    },
  },
  mounted() {
    this.retrieveUserData();

    // Initialize CodeMirror
    this.editor = CodeMirror.fromTextArea(document.getElementById('editor'), {
      lineNumbers: true,
      mode: "python",
      theme: "default",
      autoCloseBrackets: true,
      matchBrackets: true,
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,  // Use spaces instead of tabs
    });
    this.editor.setValue("# Write your code here");

    // Make CodeMirror resize correctly
    window.addEventListener('resize', () => {
      this.editor.setSize('100%', '100%');
      this.editor.refresh();
    });

    // Initial sizing
    this.editor.setSize('100%', '100%');
    this.editor.refresh();
  },
  watch: {
    assistantMessages() {
      this.scrollToBottom();
    }
  }
});
