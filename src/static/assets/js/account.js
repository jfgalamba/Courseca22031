/** 
 *  Client-side validations and logic for account-related views
 */


import {
    byID,
    whenChange,
    whenClick,
} from './utils.js';

const ACCEPTED_IMAGE_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/jpeg',
];

const MAX_FILE_SIZE = 2 ** 20;  // 1 megabyte (in bytes)

window.addEventListener('load', function() {
    whenClick('profile_image_helper', () => byID('profile_image').click());
    whenChange('profile_image', function(e) {
        const file = e.target.files[0];
        if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
            throw new Error(`Unrecognized file type ${file.type}`);
        }
        if (file.size > MAX_FILE_SIZE) {
            throw new Error(`File is to big: ${file.size}`);
        }
        byID('profile_image_helper').value = byID('profile_image')
                                            .value
                                            .replace('C:\\fakepath\\', '');
    });
});