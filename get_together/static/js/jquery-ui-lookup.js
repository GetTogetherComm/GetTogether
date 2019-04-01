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
            this.searchField = $('<input type="text" class="ui-lookup-search border border-primary" placeholder="Search" style="width: 100%;">');
            //this._addClass( this.searchField, "ui-selectmenu-menu", "ui-front" );
            this.searchField.keyup(function() {
                self.options.search(this.value, function(searchText, results){
                    if (searchText != self.searchField[0].value) return ;

                    self.current_data = results;
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
        },
        open: function(event) {
            this._super()
            this.searchField.focus()
        },
        _select: function( item, event ) {
            var oldIndex = this.element[ 0 ].selectedIndex;

            // Change native select element
            this.element[ 0 ].selectedIndex = item.index;
            this.buttonItem.replaceWith( this.buttonItem = this._renderButtonItem( item ) );
            this._setAria( item );

            // Get lookup data for this item
            var data = this.current_data[item.index-1]

            this._trigger( "select", event, { item: item, data: data } );
            this.element.trigger("select");

            if ( item.index !== oldIndex ) {
                this._trigger( "change", event, { item: item } );
                this.element.trigger("change");
            }

            this.close( event );
        },
        get_data_for: function(index) {
            if (this.current_data != null && current_data.length > index) {
                return this.current_data[index];
            } else {
                return null;
            }
        },
    });

}(jQuery));
