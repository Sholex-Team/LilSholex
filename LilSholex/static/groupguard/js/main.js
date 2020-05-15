// Functions
function check () {
    const targets = elements.getTargets(this);
    for (let i = 0; i < targets.length; i++) {
        document.querySelector(
            '#' + targets[i]
        ).parentElement.parentElement.style.display = this.checked ? 'block' : 'none'
    }
}


const elements = {
    'welcome': {
        'id': document.getElementById('id_is_welcome_message'),
        'targets': ['id_welcome_message']
    },

    'antiSpam': {
        'id': document.getElementById('id_anti_spam'),
        'targets': ['id_max_messages', 'id_spam_punish', 'id_spam_time']
    },

    'reporting': {
        'id': document.getElementById('id_reporting'),
        'targets': ['id_max_reports']
    },

    'deleting': {
        'id': document.getElementById('id_deleting'),
        'targets': ['id_delete_time']
    },

    'antiTabchi': {
        'id': document.getElementById('id_anti_tabchi'),
        'targets': ['id_tabchi_time']
    },

    'autoLock': {
        'id': document.getElementById('id_auto_lock'),
        'targets': ['id_auto_lock_on', 'id_auto_lock_off']
    },

    'getTargets': function (element) {
        const keys = Object.keys(this);
        for (let i = 0; i < keys.length - 1; i++) {
            if (this[keys[i]].id === element) {
                return this[keys[i]].targets
            }
        }
    }
};


const elementsKeys = Object.keys(elements);
for (let i = 0; i < elementsKeys.length - 1; i++) {
    elements[elementsKeys[i]].id.addEventListener('change', check);
    for (let i_2 = 0; i_2 < elements[elementsKeys[i]].targets.length; i_2++) {
        document.querySelector(
            '#' + elements[elementsKeys[i]].targets[i_2]
        ).parentElement.parentElement.style.display = elements[elementsKeys[i]].id.checked ? 'block' : 'none'
    }
}