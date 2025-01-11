new Vue({
  el: '#app',
  delimiters: ['[[', ']]'], // Change delimiters to avoid conflict with Tornado
  data: {
    student_id: '',
    language: '',
    messages: [],
    question: '',
    hint: false,  // whether student explicitly asks for a hint
    editor: null,
    consoleOutput: 'This is your Console. Press "Run Code" to see your output here...',
    consoleError: '',
    loading: false,  // disables the UI while backend is computing the response
    assessmentProgress: 0, // progress bar, 0-100
    grading: false, // new data property to manage grading state
  },
  computed: {
    // Computed property to include both user and assistant messages
    chatMessages() {
      return this.messages.filter(
        msg => msg.role === 'assistant' || (msg.role === 'user' && msg.question !== ''));
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
      this.loading = true; // Disable buttons & editor
      this.grading = true; // Start grading animation
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
        // Trigger the assessment after receiving the execute response
        this.initiateAssessment(this.student_id, code);
      })
      .catch(error => {
        console.error('Error executing code:', error);
        this.consoleError = 'Error executing code.';
        this.loading = false;
        this.grading = false; // Stop grading animation on error
      });
    },
    // Updates the CodeMirror editor and console output based on the last user message
    updateEditorAndConsole(messages) {
      this.messages = messages;
      if (!messages || !Array.isArray(messages) || messages.length === 0) return;

      const lastUserMessage = messages.slice().reverse().find(msg => msg.role === 'user');
      console.log("Last User Message:", lastUserMessage);
      if (lastUserMessage && "code" in lastUserMessage) {
        this.editor.setValue(lastUserMessage.code);
        this.consoleOutput = lastUserMessage.consoleOutput || '';
        this.consoleError = lastUserMessage.consoleError || '';
        this.question = ''; // Reset question
      }
      this.loading = false;  // Show buttons and editors
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
    // Initialization after retrieving user data
    afterRetrieveUserData(){
      // Fetch initial messages from the backend
      this.loading = true; // Disable buttons & editor
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
        console.log("Messages afterRetrieveUserData:", data.messages);
        if (data.messages && Array.isArray(data.messages)) {
          this.updateEditorAndConsole(data.messages);
        } else {
          console.error('No messages found in init response.');
        }
      })
      .catch(error => {
        console.error('Error initializing messages:', error);
        // Optionally, notify the user about the initialization failure
        this.consoleError = 'Failed to load initial messages.';
        this.loading = false;
      });
    },
    downloadScript() {
      const scriptContent = this.editor.getValue();
      const blob = new Blob([scriptContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'script.js';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    initiateAssessment(studentId, code) {
      fetch('/api/assessment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: code })
      })
      .then(response => {
        if (response.ok) {
          return response.json();
        } else {
          throw new Error(`Assessment API error: ${response.status}`);
        }
      })
      .then(data => {
        if (data.score !== undefined) {
          this.assessmentProgress = data.score;
          if (data.score === 100) {
            // Trigger confetti when score is 100
            confetti({
              particleCount: 200,
              spread: 150,
              origin: { y: 0.6 }
            });
          }
        } else {
          console.error('Failed to compute assessment score.');
        }
        this.grading = false; // Stop grading animation after assessment
      })
      .catch(error => {
        console.error('Error initiating assessment:', error);
        this.consoleError = 'Error initiating assessment.';
        this.grading = false; // Stop grading animation on error
      });
    },
  },
  mounted() {
    this.retrieveUserData();

    // Initialize CodeMirror
    this.editor = CodeMirror.fromTextArea(document.getElementById('editor'), {
      lineNumbers: true,
      mode: "python", // Adjust if language changes
      theme: "default",
      autoCloseBrackets: true,
      matchBrackets: true,
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,
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
    chatMessages() {
      this.scrollToBottom();
    }
  }
});


