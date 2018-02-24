/*!
 * jQuery UI Lookup 1.0
 *
 * Copyright 2018, Michael Hall <mhall119@gmail.com>
 * Licensed under the MIT
 *
 */

(function ($) {

    $.widget('ui.lookup', $.ui.selectmenu, {

        options: $.extend({}, $.ui.selectmenu.prototype.options, {
            search: null
        }),

        _drawMenu: function() {
            this._super();
            this._drawSearch();
        },

        _drawSearch: function() {
            var self = this;
            var selectField = this.element[0];
            this.searchField = $('<input type="text" placeholder="Search" style="width: 100%;">');
            //this._addClass( this.searchField, "ui-selectmenu-menu", "ui-front" );
            this.searchField.keyup(function() {
                self.options.search(this.value, function(searchText, results){
                    if (searchText != self.searchField[0].value) return ;

                    self.element.empty();
                    var selected = " selected"
                    self.element.append('<option value="">--------</option>')
                    $.each(results, function(){
                        self.element.append('<option value="'+ this.id +'"'+ selected +'>'+ this.display + '</option>');
                        selected="";
                    });
                    self.element.lookup("refresh");
                });
            });
            this.menuWrap.prepend(this.searchField);
        }

    });

}(jQuery));
